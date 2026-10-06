from app.qualificacao.instancias import lead_repository, relogio
from app.qualificacao.models import DadosExtraidosLead, Lead
from app.qualificacao.qualificacao import atualizar_lead, criar_lead

CANAL_CHAT_WEB = "chat_web"
CONTATO_NAO_INFORMADO = "não informado"


def garantir_lead(sessao_id: str) -> Lead:
    """Cada sessão de chat é um lead (lead.id == sessao_id). Cria o lead
    na primeira mensagem do cliente."""

    lead = lead_repository.obter(sessao_id)

    if lead is not None:
        return lead

    return criar_lead(
        repository=lead_repository,
        lead_id=sessao_id,
        canal=CANAL_CHAT_WEB,
        contato=CONTATO_NAO_INFORMADO,
        relogio=relogio,
    )


def registrar_mensagem_cliente(sessao_id: str) -> Lead:
    """Marca que o cliente interagiu agora: atualiza a última interação,
    zera as tentativas de follow-up se ele voltou a responder e
    reclassifica o lead."""

    garantir_lead(sessao_id)

    return atualizar_lead(
        repository=lead_repository,
        lead_id=sessao_id,
        dados=DadosExtraidosLead(),
        relogio=relogio,
    )
