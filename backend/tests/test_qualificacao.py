from datetime import datetime, timedelta

import pytest

from app.qualificacao.campos import campos_faltantes, lead_qualificado
from app.qualificacao.models import DadosExtraidosLead, Intencao, StatusLead, Urgencia
from app.qualificacao.qualificacao import atualizar_lead, criar_lead
from app.qualificacao.repository import InMemoryLeadRepository


class RelogioFalso:

    def __init__(self, inicio: datetime):
        self._agora = inicio

    def agora(self) -> datetime:
        return self._agora

    def avancar(self, **kwargs) -> None:
        self._agora += timedelta(**kwargs)


def _repo_e_relogio():

    relogio = RelogioFalso(datetime(2026, 1, 1, 10, 0))
    repo = InMemoryLeadRepository()

    return repo, relogio


def test_cenario_compra_fica_qualificado_apos_coletar_tudo():

    repo, relogio = _repo_e_relogio()
    lead = criar_lead(
        repo,
        "lead-1",
        canal="whatsapp",
        contato="+5511999999999",
        relogio=relogio,
    )

    assert campos_faltantes(lead) == ["intencao"]
    assert not lead_qualificado(lead)

    lead = atualizar_lead(
        repo,
        "lead-1",
        DadosExtraidosLead(intencao=Intencao.COMPRA),
        relogio=relogio,
    )

    assert lead.status == StatusLead.EM_QUALIFICACAO
    assert campos_faltantes(lead) == [
        "regiao",
        "preco_max",
        "quartos_min",
        "urgencia",
    ]

    lead = atualizar_lead(
        repo,
        "lead-1",
        DadosExtraidosLead(
            regiao="Moema",
            preco_max=800000,
            quartos_min=2,
            urgencia=Urgencia.ALTA,
        ),
        relogio=relogio,
    )

    assert lead_qualificado(lead)
    assert lead.status == StatusLead.QUALIFICADO


def test_cenario_investimento_exige_campos_proprios():

    repo, relogio = _repo_e_relogio()
    criar_lead(repo, "lead-2", canal="chat_web", contato="cliente@example.com", relogio=relogio)

    lead = atualizar_lead(
        repo,
        "lead-2",
        DadosExtraidosLead(intencao=Intencao.INVESTIMENTO),
        relogio=relogio,
    )

    assert campos_faltantes(lead) == [
        "regiao",
        "perfil_cliente",
        "ticket_investimento",
        "expectativa_retorno",
    ]

    lead = atualizar_lead(
        repo,
        "lead-2",
        DadosExtraidosLead(
            regiao="São Paulo",
            perfil_cliente="Investidor experiente, busca renda passiva",
            ticket_investimento=500000,
            expectativa_retorno="8% ao ano",
        ),
        relogio=relogio,
    )

    assert lead_qualificado(lead)
    assert lead.status == StatusLead.QUALIFICADO


def test_atualizar_lead_faz_merge_sem_apagar_dados_anteriores():

    repo, relogio = _repo_e_relogio()
    criar_lead(repo, "lead-3", canal="whatsapp", contato="123", relogio=relogio)

    atualizar_lead(
        repo,
        "lead-3",
        DadosExtraidosLead(regiao="Pinheiros", quartos_min=2),
        relogio=relogio,
    )
    lead = atualizar_lead(
        repo,
        "lead-3",
        DadosExtraidosLead(preco_max=900000),
        relogio=relogio,
    )

    assert lead.regiao == "Pinheiros"
    assert lead.quartos_min == 2
    assert lead.preco_max == 900000


def test_dado_contraditorio_sobrescreve_valor_anterior():

    repo, relogio = _repo_e_relogio()
    criar_lead(repo, "lead-4", canal="whatsapp", contato="123", relogio=relogio)

    atualizar_lead(repo, "lead-4", DadosExtraidosLead(quartos_min=2), relogio=relogio)
    lead = atualizar_lead(repo, "lead-4", DadosExtraidosLead(quartos_min=3), relogio=relogio)

    assert lead.quartos_min == 3


def test_lead_que_volta_a_responder_reseta_tentativas_de_followup():

    repo, relogio = _repo_e_relogio()
    lead = criar_lead(repo, "lead-5", canal="whatsapp", contato="123", relogio=relogio)
    lead.status = StatusLead.EM_FOLLOWUP
    lead.tentativas_followup = 2
    repo.salvar(lead)

    lead = atualizar_lead(repo, "lead-5", DadosExtraidosLead(), relogio=relogio)

    assert lead.tentativas_followup == 0
    assert lead.status != StatusLead.EM_FOLLOWUP


def test_atualizar_lead_inexistente_gera_erro():

    repo, relogio = _repo_e_relogio()

    with pytest.raises(ValueError):
        atualizar_lead(repo, "nao-existe", DadosExtraidosLead(), relogio=relogio)
