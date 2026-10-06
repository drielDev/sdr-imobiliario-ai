"""Ferramentas (function calling) que ligam a conversa da Bia ao módulo
de qualificação: registrar o que o cliente contou, consultar horários
livres e agendar. O lead da conversa é sempre o da sessão atual
(ver `contexto.sessao_atual`), nunca um id escolhido pelo modelo."""

from typing import Optional

from pydantic import ValidationError

from app.integracao.contexto import sessao_atual
from app.integracao.leads_chat import garantir_lead
from app.qualificacao.agendamento import (
    ConflitoDeHorarioError,
    SlotIndisponivelError,
    tipo_sugerido_para,
)
from app.qualificacao.campos import NOMES_CAMPOS_EM_PORTUGUES, campos_faltantes
from app.qualificacao.instancias import agenda_service, lead_repository, relogio
from app.qualificacao.models import DadosExtraidosLead, Lead, StatusLead
from app.qualificacao.qualificacao import atualizar_lead

MAX_HORARIOS_SUGERIDOS = 6
HORARIOS_POR_DIA = 2

_DIAS_DA_SEMANA = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]


def _lead_da_sessao() -> Lead:

    sessao_id = sessao_atual.get()

    if sessao_id is None:
        raise RuntimeError("Ferramenta chamada fora de uma sessão de chat.")

    return garantir_lead(sessao_id)


def _formatar_horario(inicio) -> str:

    return f"{_DIAS_DA_SEMANA[inicio.weekday()]} {inicio.strftime('%d/%m')} às {inicio.strftime('%H:%M')}"


def _situacao_do_lead(lead: Lead) -> dict:

    faltantes = campos_faltantes(lead)

    return {
        "status": lead.status.value,
        "temperatura": lead.temperatura.value,
        "qualificado": not faltantes,
        "o_que_ainda_falta_descobrir": [
            NOMES_CAMPOS_EM_PORTUGUES.get(campo, campo)
            for campo in faltantes
        ],
    }


def registrar_dados_lead(
    intencao: Optional[str] = None,
    regiao: Optional[str] = None,
    preco_min: Optional[float] = None,
    preco_max: Optional[float] = None,
    quartos_min: Optional[int] = None,
    urgencia: Optional[str] = None,
    perfil_cliente: Optional[str] = None,
    ticket_investimento: Optional[float] = None,
    expectativa_retorno: Optional[str] = None,
    imovel_interesse_id: Optional[int] = None,
    nome: Optional[str] = None,
    contato: Optional[str] = None,
) -> dict:
    """Registra no CRM o que o cliente revelou sobre si mesmo. Chame sempre
    que ele contar algo novo, passando só os campos que mudaram.
    intencao: "compra", "aluguel" ou "investimento".
    regiao: bairro, zona ou cidade de interesse.
    urgencia: "alta" (quer resolver em até ~1 mês), "media" (até ~3 meses)
    ou "baixa" (sem pressa).
    perfil_cliente: ex. "família com filhos", "investidor iniciante".
    ticket_investimento: quanto pretende investir (só para investimento).
    expectativa_retorno: ex. "renda de aluguel de 0,6% ao mês".
    imovel_interesse_id: id do imóvel do catálogo que o cliente gostou.
    nome / contato: nome e telefone ou e-mail, se o cliente informar.
    Retorna a situação do lead e o que ainda falta descobrir."""

    lead = _lead_da_sessao()

    try:
        dados = DadosExtraidosLead(
            intencao=intencao,
            regiao=regiao,
            preco_min=preco_min,
            preco_max=preco_max,
            quartos_min=quartos_min,
            urgencia=urgencia,
            perfil_cliente=perfil_cliente,
            ticket_investimento=ticket_investimento,
            expectativa_retorno=expectativa_retorno,
            imovel_interesse_id=imovel_interesse_id,
        )
    except ValidationError as erro:
        return {"erro": f"Dados inválidos: {erro.errors()[0]['msg']}"}

    lead = atualizar_lead(
        repository=lead_repository,
        lead_id=lead.id,
        dados=dados,
        relogio=relogio,
    )

    if nome or contato:
        lead.nome = nome or lead.nome
        lead.contato = contato or lead.contato
        lead_repository.salvar(lead)

    return _situacao_do_lead(lead)


def listar_horarios_disponiveis() -> dict:
    """Lista os próximos horários livres na agenda para este cliente. O
    tipo de atendimento é escolhido automaticamente pelo perfil do lead
    (investimento -> especialista; imóvel específico -> visita; demais ->
    reunião com corretor). Use antes de propor horários ao cliente."""

    lead = _lead_da_sessao()
    tipo = tipo_sugerido_para(lead)

    por_dia: dict = {}

    for slot in agenda_service.listar_slots_disponiveis(tipo=tipo):

        horarios_do_dia = por_dia.setdefault(slot.inicio.date(), [])

        if len(horarios_do_dia) < HORARIOS_POR_DIA:
            horarios_do_dia.append(slot)

    sugeridos = [slot for slots in por_dia.values() for slot in slots]

    return {
        "tipo_atendimento": tipo.value,
        "horarios": [
            {"slot_id": slot.id, "quando": _formatar_horario(slot.inicio)}
            for slot in sugeridos[:MAX_HORARIOS_SUGERIDOS]
        ],
    }


def agendar_horario(slot_id: str, imovel_id: Optional[int] = None) -> dict:
    """Agenda o atendimento no horário escolhido pelo cliente. Use o
    slot_id exatamente como veio de listar_horarios_disponiveis e só
    chame depois que o cliente confirmar o horário."""

    lead = _lead_da_sessao()

    try:
        agendamento = agenda_service.agendar(
            lead=lead,
            slot_id=slot_id,
            imovel_id=imovel_id,
        )
    except (ConflitoDeHorarioError, SlotIndisponivelError) as erro:
        return {"erro": str(erro)}

    lead.status = StatusLead.AGENDADO
    lead_repository.salvar(lead)

    return {
        "agendado": True,
        "tipo": agendamento.tipo.value,
        "responsavel": agendamento.responsavel.value,
        "quando": _formatar_horario(agendamento.inicio),
    }


FERRAMENTAS_LEAD = [
    registrar_dados_lead,
    listar_horarios_disponiveis,
    agendar_horario,
]
