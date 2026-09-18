import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.qualificacao.agendamento import (
    Agendamento,
    AgendamentoNaoEncontradoError,
    ConflitoDeHorarioError,
    SlotDisponibilidade,
    SlotIndisponivelError,
    StatusAgendamento,
    TipoAgendamento,
)
from app.qualificacao.campos import campos_faltantes, proximo_campo_prioritario
from app.qualificacao.classificacao import classificar_lead
from app.qualificacao.instancias import agenda_service, followup_service, lead_repository, relogio
from app.qualificacao.models import ClassificacaoLead, DadosExtraidosLead, Lead, StatusLead
from app.qualificacao.qualificacao import atualizar_lead, criar_lead
from app.qualificacao.resumo import ResumoLead, gerar_resumo

router = APIRouter(
    prefix="/leads",
    tags=["Leads"],
)


class CriarLeadRequest(BaseModel):
    canal: str
    contato: str
    id: str | None = None


class ProximoCampoResponse(BaseModel):
    proximo_campo: str | None
    campos_faltantes: list[str]
    qualificado: bool


class AgendarRequest(BaseModel):
    slot_id: str
    tipo: TipoAgendamento | None = None
    imovel_id: int | None = None


class ReagendarRequest(BaseModel):
    novo_slot_id: str


def _obter_lead_ou_404(lead_id: str) -> Lead:

    lead = lead_repository.obter(lead_id)

    if lead is None:
        raise HTTPException(status_code=404, detail=f"Lead {lead_id!r} não encontrado.")

    return lead


def _agendamento_atual_do_lead(lead_id: str) -> Agendamento | None:

    agendamentos = [
        agendamento
        for agendamento in agenda_service.repository.listar_agendamentos()
        if agendamento.lead_id == lead_id
        and agendamento.status != StatusAgendamento.CANCELADO
    ]

    if not agendamentos:
        return None

    return max(agendamentos, key=lambda agendamento: agendamento.criado_em)


@router.post("/", response_model=Lead)
def criar(dados: CriarLeadRequest):

    lead_id = dados.id or str(uuid.uuid4())

    if lead_repository.obter(lead_id) is not None:
        raise HTTPException(status_code=409, detail=f"Lead {lead_id!r} já existe.")

    return criar_lead(
        repository=lead_repository,
        lead_id=lead_id,
        canal=dados.canal,
        contato=dados.contato,
        relogio=relogio,
    )


@router.get("/", response_model=list[Lead])
def listar():

    return lead_repository.listar()


@router.get("/{lead_id}", response_model=Lead)
def obter(lead_id: str):

    return _obter_lead_ou_404(lead_id)


@router.patch("/{lead_id}", response_model=Lead)
def atualizar(lead_id: str, dados: DadosExtraidosLead):

    _obter_lead_ou_404(lead_id)

    try:
        return atualizar_lead(
            repository=lead_repository,
            lead_id=lead_id,
            dados=dados,
            relogio=relogio,
        )
    except ValueError as erro:
        raise HTTPException(status_code=404, detail=str(erro))


@router.get("/{lead_id}/proximo-campo", response_model=ProximoCampoResponse)
def proximo_campo(lead_id: str):

    lead = _obter_lead_ou_404(lead_id)
    faltantes = campos_faltantes(lead)

    return ProximoCampoResponse(
        proximo_campo=proximo_campo_prioritario(lead),
        campos_faltantes=faltantes,
        qualificado=not faltantes,
    )


@router.get("/{lead_id}/classificacao", response_model=ClassificacaoLead)
def classificacao(lead_id: str):

    lead = _obter_lead_ou_404(lead_id)
    resultado = classificar_lead(lead, relogio=relogio)

    lead.temperatura = resultado.temperatura
    lead.motivos_classificacao = resultado.motivos
    lead_repository.salvar(lead)

    return resultado


@router.get("/{lead_id}/resumo", response_model=ResumoLead)
def resumo(lead_id: str):

    lead = _obter_lead_ou_404(lead_id)
    agendamento = _agendamento_atual_do_lead(lead_id)

    return gerar_resumo(lead, agendamento)


@router.get("/agendamentos/slots", response_model=list[SlotDisponibilidade])
def listar_slots(tipo: TipoAgendamento | None = None, a_partir_de: datetime | None = None):

    return agenda_service.listar_slots_disponiveis(tipo=tipo, a_partir_de=a_partir_de)


@router.post("/{lead_id}/agendamentos", response_model=Agendamento)
def agendar(lead_id: str, dados: AgendarRequest):

    lead = _obter_lead_ou_404(lead_id)

    try:
        agendamento = agenda_service.agendar(
            lead=lead,
            slot_id=dados.slot_id,
            tipo=dados.tipo,
            imovel_id=dados.imovel_id,
        )
    except (ConflitoDeHorarioError, SlotIndisponivelError) as erro:
        raise HTTPException(status_code=409, detail=str(erro))

    lead.status = StatusLead.AGENDADO
    lead_repository.salvar(lead)

    return agendamento


@router.patch("/agendamentos/{agendamento_id}/reagendar", response_model=Agendamento)
def reagendar(agendamento_id: str, dados: ReagendarRequest):

    try:
        return agenda_service.reagendar(agendamento_id, dados.novo_slot_id)
    except AgendamentoNaoEncontradoError as erro:
        raise HTTPException(status_code=404, detail=str(erro))
    except (ConflitoDeHorarioError, SlotIndisponivelError) as erro:
        raise HTTPException(status_code=409, detail=str(erro))


@router.delete("/agendamentos/{agendamento_id}", response_model=Agendamento)
def cancelar(agendamento_id: str):

    try:
        return agenda_service.cancelar(agendamento_id)
    except AgendamentoNaoEncontradoError as erro:
        raise HTTPException(status_code=404, detail=str(erro))


@router.get("/followup/elegiveis")
def followup_elegiveis():

    return followup_service.leads_elegiveis_agora()


@router.post("/{lead_id}/followup/tentativa", response_model=Lead)
def registrar_tentativa_followup(lead_id: str):

    _obter_lead_ou_404(lead_id)

    try:
        return followup_service.registrar_tentativa(lead_id)
    except ValueError as erro:
        raise HTTPException(status_code=404, detail=str(erro))
