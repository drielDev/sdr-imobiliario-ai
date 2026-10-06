"""Orquestra uma mensagem do cliente: garante o lead da sessão, registra
a interação e passa a mensagem para a Bia, que tem as ferramentas de
catálogo (Pessoa 2) e de lead/agenda (Pessoa 3) à disposição."""

from threading import Lock

from app.agente.agente import AgenteSDR
from app.integracao.contexto import sessao_atual
from app.integracao.leads_chat import registrar_mensagem_cliente
from app.integracao.tools_lead import FERRAMENTAS_LEAD

_agente: AgenteSDR | None = None
_lock_agente = Lock()


def obter_agente() -> AgenteSDR:
    """Instância única da Bia, compartilhada entre o chat e o follow-up.
    Levanta RuntimeError se a GEMINI_API_KEY não estiver configurada."""

    global _agente

    with _lock_agente:

        if _agente is None:
            _agente = AgenteSDR(ferramentas_extras=FERRAMENTAS_LEAD)

        return _agente


def atender(sessao_id: str, mensagem: str) -> str:

    agente = obter_agente()

    registrar_mensagem_cliente(sessao_id)

    token = sessao_atual.set(sessao_id)

    try:
        return agente.responder(sessao_id=sessao_id, mensagem=mensagem)
    finally:
        sessao_atual.reset(token)
