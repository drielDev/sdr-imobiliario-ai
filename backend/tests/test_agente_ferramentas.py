import sys
import types as modulos
from typing import Optional

import pytest

# O catálogo real carrega o modelo de embeddings na importação.
if "app.catalogo.instancias" not in sys.modules:
    _stub_catalogo = modulos.ModuleType("app.catalogo.instancias")
    _stub_catalogo.rag = None
    _stub_catalogo.service = None
    sys.modules["app.catalogo.instancias"] = _stub_catalogo

from google.genai import types  # noqa: E402

from app.agente.agente import RESPOSTA_SEM_TEXTO, AgenteSDR  # noqa: E402

chamadas_recebidas: list[dict] = []


def ferramenta_teste(preco_max: Optional[float] = None, quartos_min: Optional[int] = None) -> dict:
    """Ferramenta de teste."""

    chamadas_recebidas.append({"preco_max": preco_max, "quartos_min": quartos_min})
    return {"ok": True}


def _resposta_com_chamada(**argumentos) -> types.GenerateContentResponse:
    return types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            function_call=types.FunctionCall(
                                name="ferramenta_teste",
                                args=argumentos,
                            )
                        )
                    ],
                )
            )
        ]
    )


def _resposta_texto(texto: str) -> types.GenerateContentResponse:
    return types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                content=types.Content(role="model", parts=[types.Part(text=texto)])
            )
        ]
    )


class ChatFalso:
    """Devolve as respostas roteirizadas e guarda o que o agente enviou."""

    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.enviados = []

    def send_message(self, mensagem):
        self.enviados.append(mensagem)
        return self.respostas.pop(0)


@pytest.fixture
def agente(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    chamadas_recebidas.clear()
    return AgenteSDR(ferramentas_extras=[ferramenta_teste])


def _conversar(monkeypatch, agente, respostas) -> tuple[str, ChatFalso]:
    chat = ChatFalso(respostas)
    monkeypatch.setattr(agente, "_obter_sessao", lambda sessao_id: chat)
    return agente.responder("sessao", "Quero um imóvel até 1 milhão"), chat


@pytest.mark.parametrize("valor", [1000000, 1000000.0, "1000000"])
def test_preco_inteiro_decimal_ou_texto_e_aceito(monkeypatch, agente, valor):

    resposta, chat = _conversar(
        monkeypatch,
        agente,
        [_resposta_com_chamada(preco_max=valor, quartos_min=3), _resposta_texto("Achei!")],
    )

    assert resposta == "Achei!"
    assert chamadas_recebidas == [{"preco_max": 1000000.0, "quartos_min": 3}]

    retorno = chat.enviados[1][0].function_response
    assert retorno.name == "ferramenta_teste"
    assert retorno.response == {"resultado": {"ok": True}}


def test_argumento_invalido_volta_como_erro_para_o_modelo(monkeypatch, agente):

    resposta, chat = _conversar(
        monkeypatch,
        agente,
        [_resposta_com_chamada(preco_max="um milhão"), _resposta_texto("Pode confirmar o valor?")],
    )

    assert resposta == "Pode confirmar o valor?"
    assert chamadas_recebidas == []
    assert "erro" in chat.enviados[1][0].function_response.response


def test_resposta_sem_texto_usa_mensagem_padrao(monkeypatch, agente):

    resposta, _ = _conversar(
        monkeypatch,
        agente,
        [_resposta_com_chamada(preco_max=1), _resposta_texto("")],
    )

    assert resposta == RESPOSTA_SEM_TEXTO
