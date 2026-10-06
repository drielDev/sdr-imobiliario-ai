"""Disparo efetivo do follow-up. O módulo de qualificação decide quem
recebe e qual mensagem; aqui implementamos o canal (o próprio chat) e o
job periódico que roda dentro da API."""

import asyncio
import logging
from datetime import datetime
from threading import Lock

from app.agente.agente import MODELO_PADRAO
from app.integracao.atendimento import obter_agente
from app.qualificacao.campos import proximo_campo_prioritario
from app.qualificacao.config import (
    CONTEXTO_PADRAO_FOLLOWUP,
    MAX_TENTATIVAS_FOLLOWUP,
    TEMPLATES_FOLLOWUP,
    TONS_FOLLOWUP,
)
from app.qualificacao.instancias import followup_service, lead_repository, relogio
from app.qualificacao.models import Lead, StatusLead

logger = logging.getLogger("integracao")

_STATUS_SEM_FOLLOWUP = (
    StatusLead.INATIVO,
    StatusLead.PERDIDO,
    StatusLead.AGENDADO,
)

# Os templates de follow-up são lidos pelo cliente, então o que falta é
# descrito falando com ele (os rótulos de `campos.py` são para o corretor).
_PERGUNTA_AO_CLIENTE: dict[str, str] = {
    "intencao": "se você quer comprar, alugar ou investir",
    "regiao": "qual região você prefere",
    "preco_max": "qual faixa de valor cabe no seu orçamento",
    "quartos_min": "quantos quartos você precisa",
    "urgencia": "para quando você precisa do imóvel",
    "perfil_cliente": "um pouco mais sobre o seu perfil como investidor",
    "ticket_investimento": "quanto você pretende investir",
    "expectativa_retorno": "qual retorno você espera do investimento",
}

PROMPT_FOLLOWUP = """
Você é a Bia, SDR de uma imobiliária. O cliente desta conversa parou de
responder e você vai mandar a tentativa {tentativa} de {maximo} de
retomar o contato. Tom desta tentativa: {tom}.

Escreva UMA mensagem curta (no máximo 2 frases), natural e em português
do Brasil, retomando de onde a conversa parou — cite o que o cliente já
contou, sem repetir perguntas já respondidas. {gancho}
Não invente imóveis, preços nem horários. Responda só com o texto da
mensagem.

Conversa até agora:
{conversa}
"""


class GeradorFollowUpBia:
    """Implementa o `GeradorTextoFollowUp` da qualificação: a Bia escreve o
    follow-up a partir da conversa real. Se a LLM falhar (ou não houver
    conversa), cai no template padrão, falando com o cliente."""

    def gerar(self, lead: Lead, numero_tentativa: int) -> str:

        campo = proximo_campo_prioritario(lead)

        try:
            agente = obter_agente()
            historico = agente.historico(lead.id)

            if historico:
                return self._gerar_com_llm(agente, historico, lead, numero_tentativa, campo)
        except Exception:
            logger.exception("Falha ao gerar follow-up com IA para o lead %s", lead.id)

        template = TEMPLATES_FOLLOWUP.get(
            numero_tentativa,
            TEMPLATES_FOLLOWUP[MAX_TENTATIVAS_FOLLOWUP],
        )

        return template.format(
            contexto=_PERGUNTA_AO_CLIENTE.get(campo, CONTEXTO_PADRAO_FOLLOWUP)
        )

    def _gerar_com_llm(self, agente, historico, lead, numero_tentativa, campo) -> str:

        conversa = "\n".join(
            f"{'Cliente' if mensagem['papel'] == 'user' else 'Bia'}: {mensagem['texto']}"
            for mensagem in historico
        )

        gancho = (
            f"Termine perguntando {_PERGUNTA_AO_CLIENTE[campo]}."
            if campo in _PERGUNTA_AO_CLIENTE
            else "Termine oferecendo um próximo passo (mais opções ou agendar uma conversa)."
        )

        resposta = agente.client.models.generate_content(
            model=MODELO_PADRAO,
            contents=PROMPT_FOLLOWUP.format(
                tentativa=numero_tentativa,
                maximo=MAX_TENTATIVAS_FOLLOWUP,
                tom=TONS_FOLLOWUP.get(numero_tentativa, ""),
                gancho=gancho,
                conversa=conversa,
            ),
        )

        texto = (resposta.text or "").strip()

        if not texto:
            raise ValueError("LLM devolveu follow-up vazio")

        return texto


gerador_followup = GeradorFollowUpBia()


class CanalChat:
    """Implementa o `CanalNotificacao` da qualificação entregando o
    follow-up no próprio chat: a mensagem entra no histórico da Bia (ela
    mantém o contexto quando o cliente responder) e fica numa caixa de
    saída que o frontend consulta periodicamente."""

    def __init__(self):
        self._pendentes: dict[str, list[dict]] = {}
        self._lock = Lock()

    def enviar(self, lead: Lead, mensagem: str) -> None:

        with self._lock:
            self._pendentes.setdefault(lead.id, []).append(
                {
                    "texto": mensagem,
                    "enviada_em": relogio.agora().isoformat(),
                }
            )

        try:
            obter_agente().adicionar_mensagem_agente(lead.id, mensagem)
        except RuntimeError as erro:
            logger.warning("Follow-up do lead %s sem contexto no agente: %s", lead.id, erro)

        logger.info("Follow-up entregue no chat do lead %s", lead.id)

    def retirar_pendentes(self, sessao_id: str) -> list[dict]:

        with self._lock:
            return self._pendentes.pop(sessao_id, [])


canal_chat = CanalChat()


def executar_followups_pendentes() -> list[str]:
    """Envia a próxima tentativa para todo lead que está no momento certo
    de receber follow-up. Retorna os ids dos leads contatados."""

    contatados = []

    for estrategia in followup_service.leads_elegiveis_agora():
        followup_service.executar_followup(
            estrategia.lead_id,
            canal_chat,
            gerador_followup,
        )
        contatados.append(estrategia.lead_id)

    return contatados


def forcar_followup(lead_id: str) -> Lead:
    """Dispara a próxima tentativa agora, sem esperar o intervalo de
    inatividade (usado pelo dashboard e na demonstração)."""

    lead = lead_repository.obter(lead_id)

    if lead is None:
        raise LookupError(f"Lead {lead_id!r} não encontrado.")

    if lead.status in _STATUS_SEM_FOLLOWUP:
        raise ValueError(f"Lead com status {lead.status.value!r} não recebe follow-up.")

    if lead.tentativas_followup >= MAX_TENTATIVAS_FOLLOWUP:
        raise ValueError("Lead já esgotou as tentativas de follow-up.")

    return followup_service.executar_followup(lead_id, canal_chat, gerador_followup)


async def loop_followup(intervalo_segundos: float) -> None:

    logger.info("Job de follow-up ativo (a cada %ss)", intervalo_segundos)

    while True:

        await asyncio.sleep(intervalo_segundos)

        try:
            contatados = await asyncio.to_thread(executar_followups_pendentes)
        except Exception:
            logger.exception("Falha ao executar follow-ups pendentes")
            continue

        if contatados:
            logger.info(
                "%s follow-up(s) enviados em %s",
                len(contatados),
                datetime.now().isoformat(timespec="seconds"),
            )
