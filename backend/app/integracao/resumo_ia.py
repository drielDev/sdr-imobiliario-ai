"""Implementa o `EnriquecedorLLM` do resumo: lê a conversa do lead com a
Bia e pede ao Gemini os pontos relevantes para o corretor."""

import json
import logging

from google.genai import types

from app.agente.agente import MODELO_PADRAO, AgenteSDR
from app.qualificacao.models import Lead

logger = logging.getLogger("integracao")

MAX_PONTOS = 5

PROMPT_RESUMO = """
Você está ajudando um corretor de imóveis a se preparar para atender um
cliente. Abaixo está a conversa do cliente com a assistente virtual.

Liste de 3 a {max_pontos} pontos curtos e objetivos que o corretor
precisa saber: o que o cliente procura, restrições, objeções, imóveis que
chamaram a atenção, sinais de urgência e qualquer detalhe pessoal útil
para a abordagem. Só use o que está na conversa — não invente nada.

Conversa:
{conversa}
"""


class EnriquecedorGemini:

    def __init__(self, agente: AgenteSDR):
        self.agente = agente

    def pontos_relevantes(self, lead: Lead) -> list[str]:

        historico = self.agente.historico(lead.id)

        if not historico:
            return []

        conversa = "\n".join(
            f"{'Cliente' if mensagem['papel'] == 'user' else 'Assistente'}: {mensagem['texto']}"
            for mensagem in historico
        )

        try:
            resposta = self.agente.client.models.generate_content(
                model=MODELO_PADRAO,
                contents=PROMPT_RESUMO.format(max_pontos=MAX_PONTOS, conversa=conversa),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=list[str],
                ),
            )
            pontos = json.loads(resposta.text)
        except Exception:
            logger.exception("Não foi possível gerar o resumo com IA do lead %s", lead.id)
            return []

        return [str(ponto) for ponto in pontos][:MAX_PONTOS]
