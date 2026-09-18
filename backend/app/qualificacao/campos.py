from app.qualificacao.config import campos_obrigatorios_para
from app.qualificacao.models import Intencao, Lead, Urgencia

# Nome amigável (PT-BR) de cada campo coletável, reaproveitado pelo
# follow-up e pelo resumo para descrever o que falta sem duplicar texto.
NOMES_CAMPOS_EM_PORTUGUES: dict[str, str] = {
    "intencao": "o que o cliente está buscando (compra, aluguel ou investimento)",
    "regiao": "a região de interesse",
    "preco_max": "a faixa de orçamento",
    "quartos_min": "quantos quartos são necessários",
    "urgencia": "o prazo do cliente",
    "perfil_cliente": "o perfil do cliente como investidor",
    "ticket_investimento": "o valor que pretende investir",
    "expectativa_retorno": "a expectativa de retorno",
}


def _campo_vazio(lead: Lead, campo: str) -> bool:

    valor = getattr(lead, campo)

    if campo == "intencao":
        return valor == Intencao.INDEFINIDA

    if campo == "urgencia":
        return valor == Urgencia.INDEFINIDA

    return valor is None


def campos_faltantes(lead: Lead) -> list[str]:
    """Retorna, em ordem de prioridade, os campos obrigatórios que ainda
    não foram preenchidos para a intenção atual do lead."""

    obrigatorios = campos_obrigatorios_para(lead.intencao)

    return [
        campo
        for campo in obrigatorios
        if _campo_vazio(lead, campo)
    ]


def proximo_campo_prioritario(lead: Lead) -> str | None:
    """Indica qual campo perguntar em seguida (ou None se o lead já tem
    tudo que é obrigatório). Quem decide a frase da pergunta é o agente
    de conversa — aqui só dizemos o que falta."""

    faltantes = campos_faltantes(lead)

    return faltantes[0] if faltantes else None


def lead_qualificado(lead: Lead) -> bool:

    return len(campos_faltantes(lead)) == 0
