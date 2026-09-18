from typing import Protocol

from pydantic import BaseModel

from app.qualificacao.agendamento import Agendamento, StatusAgendamento
from app.qualificacao.campos import NOMES_CAMPOS_EM_PORTUGUES, campos_faltantes
from app.qualificacao.models import Intencao, Lead, StatusLead, Temperatura


class CriteriosBusca(BaseModel):
    regiao: str | None
    preco_min: float | None
    preco_max: float | None
    quartos_min: int | None


class AgendamentoResumo(BaseModel):
    tipo: str
    responsavel: str
    inicio: str
    status: str


class ResumoLead(BaseModel):
    lead_id: str
    canal: str
    contato: str
    intencao: Intencao
    criterios: CriteriosBusca
    urgencia: str
    perfil_cliente: str | None
    ticket_investimento: float | None
    expectativa_retorno: str | None
    status: StatusLead
    temperatura: Temperatura
    motivos_classificacao: list[str]
    campos_faltantes: list[str]
    agendamento: AgendamentoResumo | None
    proximo_passo_sugerido: str
    pontos_relevantes: list[str]


def _proximo_passo_sugerido(
    lead: Lead,
    agendamento: Agendamento | None,
) -> str:

    if agendamento is not None and agendamento.status != StatusAgendamento.CANCELADO:
        return (
            f"Aguardar o agendamento em "
            f"{agendamento.inicio.strftime('%d/%m %H:%M')} "
            f"({agendamento.tipo.value})."
        )

    if lead.status in (StatusLead.INATIVO, StatusLead.PERDIDO):
        return "Lead inativo — sem próxima ação automática no momento."

    faltantes = campos_faltantes(lead)

    if faltantes:
        descricao = NOMES_CAMPOS_EM_PORTUGUES.get(faltantes[0], faltantes[0])
        return f"Perguntar ao cliente sobre {descricao}."

    responsavel = (
        "especialista de investimentos"
        if lead.intencao == Intencao.INVESTIMENTO
        else "corretor"
    )

    return f"Lead qualificado — encaminhar para agendamento com {responsavel}."


def gerar_resumo(
    lead: Lead,
    agendamento: Agendamento | None = None,
) -> ResumoLead:
    """Monta o resumo estruturado do lead para o corretor entender
    rapidamente quem é o cliente e o que ele procura. Não depende de
    LLM: usa só os dados já coletados pelo lead."""

    agendamento_resumo = (
        AgendamentoResumo(
            tipo=agendamento.tipo.value,
            responsavel=agendamento.responsavel.value,
            inicio=agendamento.inicio.isoformat(),
            status=agendamento.status.value,
        )
        if agendamento is not None
        else None
    )

    return ResumoLead(
        lead_id=lead.id,
        canal=lead.canal,
        contato=lead.contato,
        intencao=lead.intencao,
        criterios=CriteriosBusca(
            regiao=lead.regiao,
            preco_min=lead.preco_min,
            preco_max=lead.preco_max,
            quartos_min=lead.quartos_min,
        ),
        urgencia=lead.urgencia.value,
        perfil_cliente=lead.perfil_cliente,
        ticket_investimento=lead.ticket_investimento,
        expectativa_retorno=lead.expectativa_retorno,
        status=lead.status,
        temperatura=lead.temperatura,
        motivos_classificacao=lead.motivos_classificacao,
        campos_faltantes=campos_faltantes(lead),
        agendamento=agendamento_resumo,
        proximo_passo_sugerido=_proximo_passo_sugerido(lead, agendamento),
        pontos_relevantes=[],
    )


class EnriquecedorLLM(Protocol):
    """Ponto de extensão opcional para enriquecer o resumo com um LLM
    (ex.: pontos relevantes extraídos da conversa em texto livre). O
    módulo de qualificação não acopla a nenhum provedor — quem injetar
    esse cliente decide qual usar."""

    def pontos_relevantes(self, lead: Lead) -> list[str]:
        ...


def enriquecer_resumo(
    resumo: ResumoLead,
    lead: Lead,
    enriquecedor: EnriquecedorLLM | None,
) -> ResumoLead:

    if enriquecedor is None:
        return resumo

    resumo.pontos_relevantes = enriquecedor.pontos_relevantes(lead)

    return resumo
