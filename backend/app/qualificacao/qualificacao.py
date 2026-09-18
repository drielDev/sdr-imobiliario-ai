import logging

from app.qualificacao.campos import lead_qualificado
from app.qualificacao.classificacao import classificar_lead
from app.qualificacao.models import DadosExtraidosLead, EventoContato, Lead, StatusLead
from app.qualificacao.repository import LeadRepository
from app.qualificacao.tempo import Relogio, RelogioSistema

logger = logging.getLogger("qualificacao")

_RELOGIO_PADRAO = RelogioSistema()

_STATUS_ENCERRADOS = (
    StatusLead.INATIVO,
    StatusLead.PERDIDO,
    StatusLead.AGENDADO,
)


def criar_lead(
    repository: LeadRepository,
    lead_id: str,
    canal: str,
    contato: str,
    relogio: Relogio = _RELOGIO_PADRAO,
) -> Lead:

    agora = relogio.agora()

    lead = Lead(
        id=lead_id,
        canal=canal,
        contato=contato,
        criado_em=agora,
        atualizado_em=agora,
        ultima_interacao_em=agora,
    )

    repository.salvar(lead)

    logger.info("Lead %s criado (canal=%s)", lead_id, canal)

    return lead


def atualizar_lead(
    repository: LeadRepository,
    lead_id: str,
    dados: DadosExtraidosLead,
    relogio: Relogio = _RELOGIO_PADRAO,
) -> Lead:
    """Atualiza o lead com dados já extraídos e estruturados (vindos do
    agente/LLM). Faz merge: só sobrescreve os campos que vieram
    preenchidos em `dados`, preservando o que já tinha sido coletado
    antes. Reclassifica o lead ao final."""

    lead = repository.obter(lead_id)

    if lead is None:
        raise ValueError(f"Lead {lead_id!r} não encontrado.")

    agora = relogio.agora()

    campos_atualizados = dados.model_dump(exclude_unset=True, exclude_none=True)

    for campo, valor in campos_atualizados.items():
        setattr(lead, campo, valor)

    voltou_a_responder = lead.status == StatusLead.EM_FOLLOWUP

    if campos_atualizados or voltou_a_responder:
        lead.tentativas_followup = 0

    lead.atualizado_em = agora
    lead.ultima_interacao_em = agora

    if campos_atualizados:
        lead.historico_contatos.append(
            EventoContato(
                timestamp=agora,
                tipo="atualizacao",
                detalhe=", ".join(sorted(campos_atualizados.keys())),
            )
        )

    if lead.status not in _STATUS_ENCERRADOS:

        if lead_qualificado(lead):
            if lead.status != StatusLead.QUALIFICADO:
                logger.info("Lead %s qualificado", lead.id)
            lead.status = StatusLead.QUALIFICADO
        elif lead.status in (StatusLead.NOVO, StatusLead.EM_FOLLOWUP):
            lead.status = StatusLead.EM_QUALIFICACAO

    classificacao = classificar_lead(lead, relogio=relogio)

    lead.temperatura = classificacao.temperatura
    lead.motivos_classificacao = classificacao.motivos

    repository.salvar(lead)

    return lead
