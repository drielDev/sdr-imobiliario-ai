from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agente.agente import AgenteSDR
from app.integracao.atendimento import atender, obter_agente
from app.integracao.followup import canal_chat


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


def _obter_agente() -> AgenteSDR:

    try:
        return obter_agente()
    except RuntimeError as erro:
        raise HTTPException(status_code=503, detail=str(erro))


class MensagemChat(BaseModel):
    sessao_id: str
    mensagem: str


class RespostaChat(BaseModel):
    sessao_id: str
    resposta: str


@router.post("/", response_model=RespostaChat)
def conversar(dados: MensagemChat):

    _obter_agente()

    resposta = atender(
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


@router.get("/{sessao_id}/pendentes")
def pendentes(sessao_id: str):
    """Mensagens que a Bia enviou por conta própria (follow-up) desde a
    última consulta. O frontend chama isso periodicamente."""

    return canal_chat.retirar_pendentes(sessao_id)


@router.post("/{sessao_id}/reiniciar")
def reiniciar(sessao_id: str):

    agente = _obter_agente()

    agente.reiniciar(sessao_id)

    return {"status": "sessão reiniciada"}
