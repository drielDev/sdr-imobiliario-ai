import logging
from typing import Protocol

from pydantic import BaseModel

from app.qualificacao.campos import (
    NOMES_CAMPOS_EM_PORTUGUES,
    campos_faltantes,
    proximo_campo_prioritario,
)
from app.qualificacao.classificacao import classificar_lead
from app.qualificacao.config import (
    CONTEXTO_PADRAO_FOLLOWUP,
    INTERVALOS_FOLLOWUP_MINUTOS,
    MAX_TENTATIVAS_FOLLOWUP,
    TEMPLATES_FOLLOWUP,
    TONS_FOLLOWUP,
)
from app.qualificacao.models import EventoContato, Lead, StatusLead
from app.qualificacao.repository import LeadRepository
from app.qualificacao.tempo import Relogio, RelogioSistema

logger = logging.getLogger("qualificacao")

_RELOGIO_PADRAO = RelogioSistema()

_STATUS_SEM_FOLLOWUP = (
    StatusLead.INATIVO,
    StatusLead.PERDIDO,
    StatusLead.AGENDADO,
)

class CanalNotificacao(Protocol):
    """Interface que o módulo de interface/integração (Pessoa 4) precisa
    implementar para efetivamente enviar a mensagem de follow-up
    (WhatsApp, e-mail, etc.) e para decidir quando checar
    `leads_elegiveis_agora` periodicamente (cron/job). Este módulo não
    dispara envio sozinho."""

    def enviar(self, lead: Lead, mensagem: str) -> None:
        ...


class GeradorTextoFollowUp(Protocol):
    """Ponto de extensão opcional: por padrão o texto do follow-up vem de
    um template simples parametrizado. Quem quiser que o agente de
    conversa (LLM, Pessoa 1) gere o texto pode implementar isso e passar
    pra `montar_mensagem_followup` / `FollowUpService.executar_followup`."""

    def gerar(self, lead: Lead, numero_tentativa: int) -> str:
        ...


class EstrategiaFollowUp(BaseModel):
    lead_id: str
    numero_tentativa: int
    tom_sugerido: str
    campos_faltantes: list[str]
    mensagem_sugerida: str


def montar_mensagem_followup(
    lead: Lead,
    numero_tentativa: int,
    gerador: GeradorTextoFollowUp | None = None,
) -> str:

    if gerador is not None:
        return gerador.gerar(lead, numero_tentativa)

    campo_prioritario = proximo_campo_prioritario(lead)

    contexto = (
        NOMES_CAMPOS_EM_PORTUGUES.get(campo_prioritario, CONTEXTO_PADRAO_FOLLOWUP)
        if campo_prioritario
        else CONTEXTO_PADRAO_FOLLOWUP
    )

    template = TEMPLATES_FOLLOWUP.get(
        numero_tentativa,
        TEMPLATES_FOLLOWUP[MAX_TENTATIVAS_FOLLOWUP],
    )

    return template.format(contexto=contexto)


class FollowUpService:

    def __init__(
        self,
        repository: LeadRepository,
        relogio: Relogio = _RELOGIO_PADRAO,
    ):
        self.repository = repository
        self.relogio = relogio

    def leads_elegiveis_agora(self) -> list[EstrategiaFollowUp]:
        """Retorna, com a estratégia já montada, os leads que pararam de
        responder e estão no momento certo de receber a próxima tentativa
        de follow-up. Não envia nada — só aponta quem e o quê."""

        agora = self.relogio.agora()
        elegiveis: list[EstrategiaFollowUp] = []

        for lead in self.repository.listar():

            if lead.status in _STATUS_SEM_FOLLOWUP:
                continue

            if lead.tentativas_followup >= MAX_TENTATIVAS_FOLLOWUP:
                continue

            minutos_inativo = (
                agora - lead.ultima_interacao_em
            ).total_seconds() / 60

            intervalo_necessario = INTERVALOS_FOLLOWUP_MINUTOS[
                lead.tentativas_followup
            ]

            if minutos_inativo < intervalo_necessario:
                continue

            numero_tentativa = lead.tentativas_followup + 1

            elegiveis.append(
                EstrategiaFollowUp(
                    lead_id=lead.id,
                    numero_tentativa=numero_tentativa,
                    tom_sugerido=TONS_FOLLOWUP.get(
                        numero_tentativa,
                        TONS_FOLLOWUP[MAX_TENTATIVAS_FOLLOWUP],
                    ),
                    campos_faltantes=campos_faltantes(lead),
                    mensagem_sugerida=montar_mensagem_followup(
                        lead,
                        numero_tentativa,
                    ),
                )
            )

        return elegiveis

    def registrar_tentativa(self, lead_id: str) -> Lead:
        """Marca que uma tentativa de follow-up foi disparada (a Pessoa 4
        chama isso depois de efetivamente enviar a mensagem pelo canal
        dela). Ao esgotar o número máximo de tentativas, o lead é
        encerrado (inativo) e reclassificado."""

        lead = self.repository.obter(lead_id)

        if lead is None:
            raise ValueError(f"Lead {lead_id!r} não encontrado.")

        agora = self.relogio.agora()

        lead.tentativas_followup += 1
        lead.status = StatusLead.EM_FOLLOWUP

        lead.historico_contatos.append(
            EventoContato(
                timestamp=agora,
                tipo="followup_disparado",
                detalhe=f"tentativa {lead.tentativas_followup}",
            )
        )

        logger.info(
            "Follow-up (tentativa %d) registrado para lead %s",
            lead.tentativas_followup,
            lead.id,
        )

        if lead.tentativas_followup >= MAX_TENTATIVAS_FOLLOWUP:

            lead.status = StatusLead.INATIVO

            logger.info(
                "Lead %s esgotou as tentativas de follow-up e foi "
                "marcado como inativo",
                lead.id,
            )

        classificacao = classificar_lead(lead, relogio=self.relogio)

        lead.temperatura = classificacao.temperatura
        lead.motivos_classificacao = classificacao.motivos

        self.repository.salvar(lead)

        return lead

    def executar_followup(
        self,
        lead_id: str,
        canal: CanalNotificacao,
        gerador: GeradorTextoFollowUp | None = None,
    ) -> Lead:
        """Conveniência opcional: monta a mensagem, delega o envio ao
        canal (implementado pela Pessoa 4) e registra a tentativa."""

        lead = self.repository.obter(lead_id)

        if lead is None:
            raise ValueError(f"Lead {lead_id!r} não encontrado.")

        numero_tentativa = lead.tentativas_followup + 1
        mensagem = montar_mensagem_followup(lead, numero_tentativa, gerador)

        canal.enviar(lead, mensagem)

        return self.registrar_tentativa(lead_id)
