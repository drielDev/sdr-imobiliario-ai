from app.qualificacao.models import Intencao

# Campos obrigatórios para considerar um lead qualificado, por intenção.
# Configuração declarativa: para adicionar/remover um requisito de
# qualificação, basta editar esta lista — sem mexer na lógica.
CAMPOS_OBRIGATORIOS: dict[Intencao, list[str]] = {
    Intencao.COMPRA: [
        "intencao",
        "regiao",
        "preco_max",
        "quartos_min",
        "urgencia",
    ],
    Intencao.ALUGUEL: [
        "intencao",
        "regiao",
        "preco_max",
        "quartos_min",
        "urgencia",
    ],
    Intencao.INVESTIMENTO: [
        "intencao",
        "regiao",
        "perfil_cliente",
        "ticket_investimento",
        "expectativa_retorno",
    ],
}

# Campos obrigatórios enquanto a intenção do lead ainda não foi descoberta:
# sem saber o que o cliente quer, não dá pra saber o resto do que perguntar.
CAMPOS_OBRIGATORIOS_SEM_INTENCAO: list[str] = ["intencao"]


def campos_obrigatorios_para(intencao: Intencao) -> list[str]:

    if intencao == Intencao.INDEFINIDA:
        return CAMPOS_OBRIGATORIOS_SEM_INTENCAO

    return CAMPOS_OBRIGATORIOS.get(
        intencao,
        CAMPOS_OBRIGATORIOS_SEM_INTENCAO,
    )


# --- Classificação (quente / morno / frio) ---------------------------------

PONTOS_URGENCIA = {
    "alta": 30,
    "media": 15,
    "baixa": 5,
    "indefinida": 0,
}

PONTOS_INTENCAO_CLARA = 15
PONTOS_COMPLETUDE_MAXIMO = 30
PONTOS_FAIXA_PRECO_DEFINIDA = 10
PONTOS_ENGAJAMENTO_RECENTE = 15

MINUTOS_CONSIDERADO_ENGAJADO = 24 * 60
PENALIDADE_POR_TENTATIVA_FOLLOWUP = 12
PENALIDADE_MAXIMA_FOLLOWUP = 36

LIMIAR_QUENTE = 70
LIMIAR_MORNO = 40


# --- Follow-up ---------------------------------------------------------

# Minutos de inatividade após os quais cada tentativa de follow-up deve
# disparar (índice 0 = 1ª tentativa, índice 1 = 2ª tentativa, ...).
INTERVALOS_FOLLOWUP_MINUTOS: list[int] = [60, 24 * 60, 72 * 60]

MAX_TENTATIVAS_FOLLOWUP = len(INTERVALOS_FOLLOWUP_MINUTOS)

TEMPLATES_FOLLOWUP: dict[int, str] = {
    1: (
        "Oi! Vi que você começou a buscar um imóvel por aqui e não "
        "chegamos a terminar. Podemos continuar? Só preciso saber "
        "{contexto}."
    ),
    2: (
        "Passando pra saber se você ainda tem interesse em encontrar um "
        "imóvel com a gente. Se puder me contar {contexto}, já consigo "
        "te mostrar opções."
    ),
    3: (
        "Essa é a última vez que vou insistir por aqui. Se ainda quiser "
        "ajuda, é só responder com {contexto} que retomamos de onde "
        "paramos."
    ),
}

CONTEXTO_PADRAO_FOLLOWUP = "o que você está procurando"

TONS_FOLLOWUP: dict[int, str] = {
    1: "leve e consultivo",
    2: "direto, oferecendo ajuda concreta",
    3: "cordial de despedida, deixando a porta aberta",
}


# --- Agendamento ---------------------------------------------------------

DURACAO_SLOT_MINUTOS = 60
DIAS_UTEIS_GERADOS = 5
HORARIO_INICIO = 9
HORARIO_FIM = 18
