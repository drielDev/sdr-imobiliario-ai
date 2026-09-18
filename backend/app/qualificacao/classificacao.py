import logging

from app.qualificacao.campos import campos_faltantes
from app.qualificacao.config import (
    LIMIAR_MORNO,
    LIMIAR_QUENTE,
    MINUTOS_CONSIDERADO_ENGAJADO,
    PENALIDADE_MAXIMA_FOLLOWUP,
    PENALIDADE_POR_TENTATIVA_FOLLOWUP,
    PONTOS_COMPLETUDE_MAXIMO,
    PONTOS_ENGAJAMENTO_RECENTE,
    PONTOS_FAIXA_PRECO_DEFINIDA,
    PONTOS_INTENCAO_CLARA,
    PONTOS_URGENCIA,
    campos_obrigatorios_para,
)
from app.qualificacao.models import ClassificacaoLead, Intencao, Lead, Temperatura
from app.qualificacao.tempo import Relogio, RelogioSistema

logger = logging.getLogger("qualificacao")

_RELOGIO_PADRAO = RelogioSistema()


def _faixa_de_valor_definida(lead: Lead) -> bool:

    if lead.intencao == Intencao.INVESTIMENTO:
        return lead.ticket_investimento is not None

    return lead.preco_min is not None or lead.preco_max is not None


def classificar_lead(
    lead: Lead,
    relogio: Relogio = _RELOGIO_PADRAO,
) -> ClassificacaoLead:
    """Calcula a temperatura do lead (quente/morno/frio) a partir de
    regras explicáveis e configuráveis (ver app/qualificacao/config.py).
    Não altera o lead — quem chama decide se/quando aplicar o resultado.
    Pode (e deve) ser chamada de novo sempre que o lead for atualizado ou
    quando ele for detectado como inativo, já que o fator de engajamento
    e a penalidade de follow-up mudam com o tempo."""

    pontuacao = 0
    motivos: list[str] = []

    pontos_urgencia = PONTOS_URGENCIA[lead.urgencia.value]
    pontuacao += pontos_urgencia

    if pontos_urgencia > 0:
        motivos.append(
            f"Urgência {lead.urgencia.value} (+{pontos_urgencia} pts)"
        )
    else:
        motivos.append("Urgência ainda não informada (+0 pts)")

    if lead.intencao != Intencao.INDEFINIDA:
        pontuacao += PONTOS_INTENCAO_CLARA
        motivos.append(
            f"Intenção definida: {lead.intencao.value} "
            f"(+{PONTOS_INTENCAO_CLARA} pts)"
        )
    else:
        motivos.append("Intenção ainda não identificada (+0 pts)")

    obrigatorios = campos_obrigatorios_para(lead.intencao)
    faltantes = campos_faltantes(lead)
    preenchidos = len(obrigatorios) - len(faltantes)

    proporcao = preenchidos / len(obrigatorios) if obrigatorios else 0
    pontos_completude = round(proporcao * PONTOS_COMPLETUDE_MAXIMO)
    pontuacao += pontos_completude

    motivos.append(
        f"Dados coletados: {preenchidos}/{len(obrigatorios)} campos "
        f"obrigatórios (+{pontos_completude} pts)"
    )

    if _faixa_de_valor_definida(lead):
        pontuacao += PONTOS_FAIXA_PRECO_DEFINIDA
        motivos.append(
            f"Faixa de valor já informada (+{PONTOS_FAIXA_PRECO_DEFINIDA} pts)"
        )

    minutos_desde_interacao = (
        relogio.agora() - lead.ultima_interacao_em
    ).total_seconds() / 60

    if minutos_desde_interacao <= MINUTOS_CONSIDERADO_ENGAJADO:
        pontuacao += PONTOS_ENGAJAMENTO_RECENTE
        motivos.append(
            f"Interagiu recentemente (+{PONTOS_ENGAJAMENTO_RECENTE} pts)"
        )
    else:
        horas = int(MINUTOS_CONSIDERADO_ENGAJADO / 60)
        motivos.append(f"Sem interação há mais de {horas}h (+0 pts)")

    penalidade = min(
        lead.tentativas_followup * PENALIDADE_POR_TENTATIVA_FOLLOWUP,
        PENALIDADE_MAXIMA_FOLLOWUP,
    )

    if penalidade > 0:
        pontuacao -= penalidade
        motivos.append(
            f"{lead.tentativas_followup} tentativa(s) de follow-up sem "
            f"resposta (-{penalidade} pts)"
        )

    pontuacao = max(0, min(100, pontuacao))

    if pontuacao >= LIMIAR_QUENTE:
        temperatura = Temperatura.QUENTE
    elif pontuacao >= LIMIAR_MORNO:
        temperatura = Temperatura.MORNO
    else:
        temperatura = Temperatura.FRIO

    if temperatura != lead.temperatura:
        logger.info(
            "Lead %s mudou de temperatura: %s -> %s (%d pts)",
            lead.id,
            lead.temperatura.value,
            temperatura.value,
            pontuacao,
        )

    return ClassificacaoLead(
        temperatura=temperatura,
        pontuacao=pontuacao,
        motivos=motivos,
    )
