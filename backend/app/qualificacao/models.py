from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Intencao(str, Enum):
    COMPRA = "compra"
    ALUGUEL = "aluguel"
    INVESTIMENTO = "investimento"
    INDEFINIDA = "indefinida"


class Urgencia(str, Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAIXA = "baixa"
    INDEFINIDA = "indefinida"


class Temperatura(str, Enum):
    QUENTE = "quente"
    MORNO = "morno"
    FRIO = "frio"


class StatusLead(str, Enum):
    NOVO = "novo"
    EM_QUALIFICACAO = "em_qualificacao"
    QUALIFICADO = "qualificado"
    EM_FOLLOWUP = "em_followup"
    AGENDADO = "agendado"
    INATIVO = "inativo"
    PERDIDO = "perdido"


class EventoContato(BaseModel):
    timestamp: datetime
    tipo: str
    detalhe: str = ""


class DadosExtraidosLead(BaseModel):
    """Contrato de dados estruturados vindos do módulo de agente/LLM
    (Pessoa 1) após interpretar a mensagem do cliente. Todos os campos são
    opcionais: só o que foi de fato extraído da conversa é enviado."""

    intencao: Intencao | None = None
    regiao: str | None = None
    preco_min: float | None = None
    preco_max: float | None = None
    quartos_min: int | None = None
    urgencia: Urgencia | None = None
    perfil_cliente: str | None = None
    ticket_investimento: float | None = None
    expectativa_retorno: str | None = None
    imovel_interesse_id: int | None = None


class Lead(BaseModel):
    id: str
    canal: str
    contato: str

    intencao: Intencao = Intencao.INDEFINIDA
    regiao: str | None = None
    preco_min: float | None = None
    preco_max: float | None = None
    quartos_min: int | None = None
    urgencia: Urgencia = Urgencia.INDEFINIDA
    perfil_cliente: str | None = None
    ticket_investimento: float | None = None
    expectativa_retorno: str | None = None
    imovel_interesse_id: int | None = None

    status: StatusLead = StatusLead.NOVO
    temperatura: Temperatura = Temperatura.FRIO
    motivos_classificacao: list[str] = Field(default_factory=list)

    tentativas_followup: int = 0

    criado_em: datetime
    atualizado_em: datetime
    ultima_interacao_em: datetime

    historico_contatos: list[EventoContato] = Field(default_factory=list)


class ClassificacaoLead(BaseModel):
    temperatura: Temperatura
    pontuacao: int
    motivos: list[str]
