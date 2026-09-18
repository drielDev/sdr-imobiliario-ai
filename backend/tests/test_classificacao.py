from datetime import datetime, timedelta

from app.qualificacao.classificacao import classificar_lead
from app.qualificacao.models import Intencao, Lead, Temperatura, Urgencia


class RelogioFalso:

    def __init__(self, inicio: datetime):
        self._agora = inicio

    def agora(self) -> datetime:
        return self._agora


def _lead_base(**overrides) -> Lead:

    agora = overrides.pop("agora", datetime(2026, 1, 1, 12, 0))

    dados = dict(
        id="lead-x",
        canal="whatsapp",
        contato="123",
        criado_em=agora,
        atualizado_em=agora,
        ultima_interacao_em=agora,
    )
    dados.update(overrides)

    return Lead(**dados)


def test_lead_completo_urgente_e_recente_fica_quente():

    agora = datetime(2026, 1, 1, 12, 0)
    lead = _lead_base(
        intencao=Intencao.COMPRA,
        regiao="Moema",
        preco_max=800000,
        quartos_min=2,
        urgencia=Urgencia.ALTA,
        ultima_interacao_em=agora,
    )

    resultado = classificar_lead(lead, relogio=RelogioFalso(agora))

    assert resultado.temperatura == Temperatura.QUENTE
    assert resultado.motivos


def test_lead_sem_dados_e_indefinido_fica_frio():

    agora = datetime(2026, 1, 1, 12, 0)
    lead = _lead_base(ultima_interacao_em=agora - timedelta(days=10))

    resultado = classificar_lead(lead, relogio=RelogioFalso(agora))

    assert resultado.temperatura == Temperatura.FRIO


def test_lead_parcialmente_qualificado_fica_morno():

    agora = datetime(2026, 1, 1, 12, 0)
    lead = _lead_base(
        intencao=Intencao.COMPRA,
        regiao="Moema",
        ultima_interacao_em=agora,
    )

    resultado = classificar_lead(lead, relogio=RelogioFalso(agora))

    assert resultado.temperatura == Temperatura.MORNO


def test_tentativas_de_followup_sem_resposta_penalizam_pontuacao():

    agora = datetime(2026, 1, 1, 12, 0)

    lead_engajado = _lead_base(
        intencao=Intencao.COMPRA,
        regiao="Moema",
        preco_max=800000,
        quartos_min=2,
        urgencia=Urgencia.ALTA,
        ultima_interacao_em=agora,
    )
    lead_sem_resposta = _lead_base(
        id="lead-y",
        intencao=Intencao.COMPRA,
        regiao="Moema",
        preco_max=800000,
        quartos_min=2,
        urgencia=Urgencia.ALTA,
        ultima_interacao_em=agora,
        tentativas_followup=3,
    )

    pontuacao_engajado = classificar_lead(lead_engajado, relogio=RelogioFalso(agora)).pontuacao
    pontuacao_sem_resposta = classificar_lead(lead_sem_resposta, relogio=RelogioFalso(agora)).pontuacao

    assert pontuacao_sem_resposta < pontuacao_engajado


def test_dado_contraditorio_urgencia_atualizada_muda_classificacao():

    agora = datetime(2026, 1, 1, 12, 0)
    lead = _lead_base(
        intencao=Intencao.COMPRA,
        regiao="Moema",
        preco_max=800000,
        quartos_min=2,
        urgencia=Urgencia.BAIXA,
        ultima_interacao_em=agora,
    )

    antes = classificar_lead(lead, relogio=RelogioFalso(agora))

    lead.urgencia = Urgencia.ALTA

    depois = classificar_lead(lead, relogio=RelogioFalso(agora))

    assert depois.pontuacao > antes.pontuacao
