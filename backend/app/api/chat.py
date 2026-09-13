from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agente.agente import AgenteSDR


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

_agente: AgenteSDR | None = None


def _obter_agente() -> AgenteSDR:

    global _agente

    if _agente is None:

        try:
            _agente = AgenteSDR()
        except RuntimeError as erro:
            raise HTTPException(status_code=503, detail=str(erro))

    return _agente


class MensagemChat(BaseModel):
    sessao_id: str
    mensagem: str


class RespostaChat(BaseModel):
    sessao_id: str
    resposta: str


@router.post("/", response_model=RespostaChat)
def conversar(dados: MensagemChat):

    agente = _obter_agente()

    resposta = agente.responder(
        sessao_id=dados.sessao_id,
        mensagem=dados.mensagem,
    )

    return RespostaChat(
        sessao_id=dados.sessao_id,
        resposta=resposta,
    )


@router.get("/{sessao_id}/historico")
def historico(sessao_id: str):

    agente = _obter_agente()

    return agente.historico(sessao_id)


@router.post("/{sessao_id}/reiniciar")
def reiniciar(sessao_id: str):

    agente = _obter_agente()

    agente.reiniciar(sessao_id)

    return {"status": "sessão reiniciada"}
