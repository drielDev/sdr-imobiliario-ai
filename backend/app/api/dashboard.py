from collections import Counter
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.integracao.atendimento import obter_agente
from app.integracao.followup import executar_followups_pendentes, forcar_followup
from app.integracao.resumo_ia import EnriquecedorGemini
from app.qualificacao.agendamento import Agendamento, StatusAgendamento
from app.qualificacao.campos import campos_faltantes
from app.qualificacao.config import MAX_TENTATIVAS_FOLLOWUP
from app.qualificacao.instancias import agenda_service, followup_service, lead_repository
from app.qualificacao.models import Intencao, Lead, StatusLead, Temperatura
from app.qualificacao.resumo import ResumoLead, enriquecer_resumo, gerar_resumo

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


class MetricasDashboard(BaseModel):
    total_leads: int
    leads_qualificados: int
    por_temperatura: dict[str, int]
    por_intencao: dict[str, int]
    por_status: dict[str, int]
    agendamentos_ativos: int
    followups_pendentes: int
    followups_enviados: int


class LinhaLead(BaseModel):
    id: str
    nome: str | None
    contato: str
    canal: str
    intencao: Intencao
    regiao: str | None
    temperatura: Temperatura
    status: StatusLead
    tentativas_followup: int
    max_tentativas_followup: int
    campos_faltantes: list[str]
    ultima_interacao_em: datetime
    proximo_agendamento: datetime | None


class LinhaAgendamento(BaseModel):
    agendamento: Agendamento
    lead_nome: str | None
    lead_contato: str | None


class DetalheLead(BaseModel):
    resumo: ResumoLead
    conversa: list[dict]


class ResultadoFollowUp(BaseModel):
    leads_contatados: list[str]


def _agendamentos_ativos() -> list[Agendamento]:

    return [
        agendamento
        for agendamento in agenda_service.repository.listar_agendamentos()
        if agendamento.status != StatusAgendamento.CANCELADO
    ]


def _historico_conversa(lead_id: str) -> list[dict]:

    try:
        return obter_agente().historico(lead_id)
    except RuntimeError:
        return []


@router.get("/metricas", response_model=MetricasDashboard)
def metricas():

    leads = lead_repository.listar()

    return MetricasDashboard(
        total_leads=len(leads),
        leads_qualificados=sum(1 for lead in leads if not campos_faltantes(lead)),
        por_temperatura={
            temperatura.value: sum(1 for lead in leads if lead.temperatura == temperatura)
            for temperatura in Temperatura
        },
        por_intencao=dict(Counter(lead.intencao.value for lead in leads)),
        por_status=dict(Counter(lead.status.value for lead in leads)),
        agendamentos_ativos=len(_agendamentos_ativos()),
        followups_pendentes=len(followup_service.leads_elegiveis_agora()),
        followups_enviados=sum(lead.tentativas_followup for lead in leads),
    )


@router.get("/leads", response_model=list[LinhaLead])
def leads():

    inicio_por_lead: dict[str, datetime] = {}

    for agendamento in _agendamentos_ativos():
        atual = inicio_por_lead.get(agendamento.lead_id)
        if atual is None or agendamento.inicio < atual:
            inicio_por_lead[agendamento.lead_id] = agendamento.inicio

    linhas = [
        LinhaLead(
            id=lead.id,
            nome=lead.nome,
            contato=lead.contato,
            canal=lead.canal,
            intencao=lead.intencao,
            regiao=lead.regiao,
            temperatura=lead.temperatura,
            status=lead.status,
            tentativas_followup=lead.tentativas_followup,
            max_tentativas_followup=MAX_TENTATIVAS_FOLLOWUP,
            campos_faltantes=campos_faltantes(lead),
            ultima_interacao_em=lead.ultima_interacao_em,
            proximo_agendamento=inicio_por_lead.get(lead.id),
        )
        for lead in lead_repository.listar()
    ]

    return sorted(linhas, key=lambda linha: linha.ultima_interacao_em, reverse=True)


@router.get("/agendamentos", response_model=list[LinhaAgendamento])
def agendamentos():

    linhas = []

    for agendamento in sorted(_agendamentos_ativos(), key=lambda a: a.inicio):
        lead: Lead | None = lead_repository.obter(agendamento.lead_id)
        linhas.append(
            LinhaAgendamento(
                agendamento=agendamento,
                lead_nome=lead.nome if lead else None,
                lead_contato=lead.contato if lead else None,
            )
        )

    return linhas


@router.get("/leads/{lead_id}", response_model=DetalheLead)
def detalhe_lead(lead_id: str, com_ia: bool = False):
    """Resumo para o corretor + conversa completa. Com `com_ia=true`, o
    Gemini lê a conversa e preenche os pontos relevantes."""

    lead = lead_repository.obter(lead_id)

    if lead is None:
        raise HTTPException(status_code=404, detail=f"Lead {lead_id!r} não encontrado.")

    agendamentos_do_lead = [
        agendamento
        for agendamento in _agendamentos_ativos()
        if agendamento.lead_id == lead_id
    ]
    agendamento = max(agendamentos_do_lead, key=lambda a: a.criado_em, default=None)

    resumo = gerar_resumo(lead, agendamento)

    if com_ia:
        try:
            enriquecedor = EnriquecedorGemini(obter_agente())
        except RuntimeError as erro:
            raise HTTPException(status_code=503, detail=str(erro))
        resumo = enriquecer_resumo(resumo, lead, enriquecedor)

    return DetalheLead(resumo=resumo, conversa=_historico_conversa(lead_id))


@router.post("/followup/executar", response_model=ResultadoFollowUp)
def executar_followup_pendentes():
    """Executa agora a rodada de follow-up que o job faz periodicamente."""

    return ResultadoFollowUp(leads_contatados=executar_followups_pendentes())


@router.post("/leads/{lead_id}/followup", response_model=Lead)
def disparar_followup(lead_id: str):
    """Envia a próxima tentativa de follow-up para o lead sem esperar o
    intervalo de inatividade (útil na demonstração)."""

    try:
        return forcar_followup(lead_id)
    except LookupError as erro:
        raise HTTPException(status_code=404, detail=str(erro))
    except ValueError as erro:
        raise HTTPException(status_code=409, detail=str(erro))
