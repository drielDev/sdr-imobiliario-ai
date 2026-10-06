import sys
import types
import uuid

import pytest

# O catálogo real carrega o modelo de embeddings (bge-m3) na importação.
# Estes testes cobrem só a integração chat -> lead -> agenda -> follow-up,
# então trocamos as instâncias do catálogo por um stub vazio.
if "app.catalogo.instancias" not in sys.modules:
    _stub_catalogo = types.ModuleType("app.catalogo.instancias")
    _stub_catalogo.rag = None
    _stub_catalogo.service = None
    sys.modules["app.catalogo.instancias"] = _stub_catalogo

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.api.chat import router as chat_router  # noqa: E402
from app.api.dashboard import router as dashboard_router  # noqa: E402
from app.integracao import atendimento  # noqa: E402
from app.integracao.followup import canal_chat, forcar_followup  # noqa: E402
from app.integracao.tools_lead import (  # noqa: E402
    agendar_horario,
    listar_horarios_disponiveis,
    registrar_dados_lead,
)
from app.qualificacao.instancias import lead_repository  # noqa: E402
from app.qualificacao.models import Intencao, StatusLead  # noqa: E402


class AgenteFalso:
    """Faz o papel do Gemini: em vez de interpretar a mensagem, executa um
    roteiro de chamadas de ferramenta definido pelo teste."""

    def __init__(self):
        self.roteiro = []
        self.historicos: dict[str, list[dict]] = {}

    def responder(self, sessao_id: str, mensagem: str) -> str:
        historico = self.historicos.setdefault(sessao_id, [])
        historico.append({"papel": "user", "texto": mensagem})

        for ferramenta, argumentos in self.roteiro:
            ferramenta(**argumentos)

        historico.append({"papel": "model", "texto": "ok"})
        return "ok"

    def adicionar_mensagem_agente(self, sessao_id: str, mensagem: str) -> None:
        self.historicos.setdefault(sessao_id, []).append(
            {"papel": "model", "texto": mensagem}
        )

    def historico(self, sessao_id: str) -> list[dict]:
        return self.historicos.get(sessao_id, [])

    def reiniciar(self, sessao_id: str) -> None:
        self.historicos.pop(sessao_id, None)


@pytest.fixture
def agente(monkeypatch):
    falso = AgenteFalso()
    monkeypatch.setattr(atendimento, "_agente", falso)
    return falso


@pytest.fixture
def cliente():
    app = FastAPI()
    app.include_router(chat_router)
    app.include_router(dashboard_router)
    return TestClient(app)


def _sessao() -> str:
    return f"teste-{uuid.uuid4()}"


def test_primeira_mensagem_cria_lead_e_ferramenta_atualiza_lead_da_sessao(agente):

    sessao = _sessao()
    agente.roteiro = [
        (registrar_dados_lead, {"intencao": "compra", "regiao": "Zona Sul", "nome": "Ana"}),
    ]

    atendimento.atender(sessao, "Procuro apartamento na zona sul")

    lead = lead_repository.obter(sessao)
    assert lead is not None
    assert lead.canal == "chat_web"
    assert lead.intencao == Intencao.COMPRA
    assert lead.regiao == "Zona Sul"
    assert lead.nome == "Ana"
    assert lead.status == StatusLead.EM_QUALIFICACAO


def test_registrar_dados_lead_devolve_o_que_falta_e_rejeita_valor_invalido(agente):

    sessao = _sessao()
    retornos = []
    agente.roteiro = [
        (lambda: retornos.append(registrar_dados_lead(intencao="compra", preco_max=700000)), {}),
        (lambda: retornos.append(registrar_dados_lead(urgencia="ontem")), {}),
    ]

    atendimento.atender(sessao, "Quero comprar, até 700 mil")

    situacao, invalido = retornos
    assert situacao["qualificado"] is False
    assert "a região de interesse" in situacao["o_que_ainda_falta_descobrir"]
    assert "erro" in invalido


def test_fluxo_compra_qualifica_lista_horarios_e_agenda(agente):

    sessao = _sessao()
    horarios = {}
    agente.roteiro = [
        (
            registrar_dados_lead,
            {
                "intencao": "compra",
                "regiao": "Moema",
                "preco_max": 900000,
                "quartos_min": 3,
                "urgencia": "alta",
                "contato": "11 99999-0000",
            },
        ),
        (lambda: horarios.update(listar_horarios_disponiveis()), {}),
    ]

    atendimento.atender(sessao, "Quero comprar em Moema, 3 quartos, até 900 mil, urgente")

    assert lead_repository.obter(sessao).status == StatusLead.QUALIFICADO
    assert horarios["tipo_atendimento"] == "reuniao_corretor"
    assert 0 < len(horarios["horarios"]) <= 6

    resultado = agendar_horario_na_sessao(agente, sessao, horarios["horarios"][0]["slot_id"])

    assert resultado["agendado"] is True
    lead = lead_repository.obter(sessao)
    assert lead.status == StatusLead.AGENDADO
    assert lead.contato == "11 99999-0000"


def agendar_horario_na_sessao(agente, sessao, slot_id):

    resultado = {}
    agente.roteiro = [(lambda: resultado.update(agendar_horario(slot_id=slot_id)), {})]
    atendimento.atender(sessao, "Pode ser nesse horário")
    return resultado


def test_investimento_e_direcionado_para_especialista(agente):

    sessao = _sessao()
    horarios = {}
    agente.roteiro = [
        (registrar_dados_lead, {"intencao": "investimento", "ticket_investimento": 500000}),
        (lambda: horarios.update(listar_horarios_disponiveis()), {}),
    ]

    atendimento.atender(sessao, "Quero investir em imóveis para renda")

    assert horarios["tipo_atendimento"] == "reuniao_especialista"


def test_followup_entra_no_contexto_da_bia_e_na_caixa_do_chat(agente, cliente):

    sessao = _sessao()
    agente.roteiro = [(registrar_dados_lead, {"intencao": "aluguel"})]
    atendimento.atender(sessao, "Quero alugar")

    lead = forcar_followup(sessao)

    assert lead.tentativas_followup == 1
    assert lead.status == StatusLead.EM_FOLLOWUP
    assert agente.historico(sessao)[-1]["papel"] == "model"

    pendentes = cliente.get(f"/chat/{sessao}/pendentes").json()
    assert len(pendentes) == 1
    # sem LLM disponível, cai no template falando com o cliente
    assert "qual região você prefere" in pendentes[0]["texto"]
    assert pendentes[0]["texto"] == agente.historico(sessao)[-1]["texto"]
    assert cliente.get(f"/chat/{sessao}/pendentes").json() == []

    # cliente volta a responder: tentativas zeram e o lead sai do follow-up
    agente.roteiro = []
    atendimento.atender(sessao, "Oi, voltei")
    lead = lead_repository.obter(sessao)
    assert lead.tentativas_followup == 0
    assert lead.status == StatusLead.EM_QUALIFICACAO


def test_lead_agendado_nao_recebe_followup(agente):

    sessao = _sessao()
    atendimento.atender(sessao, "Oi")
    lead = lead_repository.obter(sessao)
    lead.status = StatusLead.AGENDADO
    lead_repository.salvar(lead)

    with pytest.raises(ValueError):
        forcar_followup(sessao)

    assert canal_chat.retirar_pendentes(sessao) == []


def test_dashboard_expoe_metricas_leads_e_detalhe(agente, cliente):

    sessao = _sessao()
    agente.roteiro = [(registrar_dados_lead, {"intencao": "compra", "nome": "Bruno"})]
    atendimento.atender(sessao, "Quero comprar um apartamento")

    metricas = cliente.get("/dashboard/metricas").json()
    assert metricas["total_leads"] >= 1
    assert sum(metricas["por_temperatura"].values()) == metricas["total_leads"]

    linhas = cliente.get("/dashboard/leads").json()
    linha = next(linha for linha in linhas if linha["id"] == sessao)
    assert linha["nome"] == "Bruno"
    assert linha["intencao"] == "compra"

    detalhe = cliente.get(f"/dashboard/leads/{sessao}").json()
    assert detalhe["resumo"]["lead_id"] == sessao
    assert [m["papel"] for m in detalhe["conversa"]] == ["user", "model"]

    assert cliente.get("/dashboard/leads/nao-existe").status_code == 404
    assert cliente.post("/dashboard/leads/nao-existe/followup").status_code == 404
