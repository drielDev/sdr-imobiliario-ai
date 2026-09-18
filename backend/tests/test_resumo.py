from datetime import datetime

from app.qualificacao.agendamento import (
    Agendamento,
    ResponsavelTipo,
    TipoAgendamento,
)
from app.qualificacao.models import Intencao, Lead, StatusLead, Urgencia
from app.qualificacao.resumo import enriquecer_resumo, gerar_resumo


def _lead(**overrides) -> Lead:

    agora = datetime(2026, 1, 1, 10, 0)

    dados = dict(
        id="lead-1",
        canal="whatsapp",
        contato="123",
        criado_em=agora,
        atualizado_em=agora,
        ultima_interacao_em=agora,
    )
    dados.update(overrides)

    return Lead(**dados)


def test_resumo_deterministico_sem_dados_sugere_pergunta():

    lead = _lead(intencao=Intencao.COMPRA, regiao="Moema")

    resumo = gerar_resumo(lead)

    assert resumo.campos_faltantes
    assert "Perguntar" in resumo.proximo_passo_sugerido


def test_resumo_de_lead_qualificado_sugere_encaminhar_para_corretor():

    lead = _lead(
        intencao=Intencao.COMPRA,
        regiao="Moema",
        preco_max=800000,
        quartos_min=2,
        urgencia=Urgencia.ALTA,
    )

    resumo = gerar_resumo(lead)

    assert not resumo.campos_faltantes
    assert "corretor" in resumo.proximo_passo_sugerido


def test_resumo_de_lead_investimento_qualificado_sugere_especialista():

    lead = _lead(
        intencao=Intencao.INVESTIMENTO,
        regiao="São Paulo",
        perfil_cliente="Investidor experiente",
        ticket_investimento=500000,
        expectativa_retorno="8% ao ano",
    )

    resumo = gerar_resumo(lead)

    assert not resumo.campos_faltantes
    assert "especialista" in resumo.proximo_passo_sugerido


def test_resumo_com_agendamento_confirmado_mostra_proximo_passo_de_espera():

    lead = _lead(intencao=Intencao.COMPRA, status=StatusLead.AGENDADO)
    agendamento = Agendamento(
        id="agenda-1",
        lead_id="lead-1",
        slot_id="slot-1",
        tipo=TipoAgendamento.REUNIAO_CORRETOR,
        responsavel=ResponsavelTipo.CORRETOR,
        inicio=datetime(2026, 1, 5, 10, 0),
        fim=datetime(2026, 1, 5, 11, 0),
        criado_em=datetime(2026, 1, 1, 10, 0),
    )

    resumo = gerar_resumo(lead, agendamento)

    assert resumo.agendamento is not None
    assert "Aguardar" in resumo.proximo_passo_sugerido


def test_enriquecer_resumo_com_llm_opcional():

    class EnriquecedorFalso:
        def pontos_relevantes(self, lead):
            return ["Cliente mencionou que já visitou o imóvel antes"]

    lead = _lead()
    resumo = gerar_resumo(lead)
    resumo = enriquecer_resumo(resumo, lead, EnriquecedorFalso())

    assert resumo.pontos_relevantes == [
        "Cliente mencionou que já visitou o imóvel antes"
    ]


def test_enriquecer_resumo_sem_llm_mantem_vazio():

    lead = _lead()
    resumo = gerar_resumo(lead)
    resumo = enriquecer_resumo(resumo, lead, None)

    assert resumo.pontos_relevantes == []
