import logging
import os

from google import genai
from google.genai import types
from pydantic import ValidationError, validate_call

from app.agente.prompts import SYSTEM_PROMPT
from app.agente.tools import buscar_imoveis_estruturado, buscar_imoveis_semantico

MODELO_PADRAO = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Limite de rodadas de ferramenta por mensagem (evita loop infinito).
MAX_RODADAS_FERRAMENTAS = 10

RESPOSTA_SEM_TEXTO = (
    "Desculpe, me enrolei aqui do meu lado. Pode repetir o que você "
    "procura, por favor?"
)

logger = logging.getLogger("agente")


class AgenteSDR:

    def __init__(self, ferramentas_extras: list | None = None):

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY não configurada. Defina a variável de "
                "ambiente (ou crie um arquivo .env) com sua chave da API "
                "do Gemini."
            )

        self.client = genai.Client(api_key=api_key)

        ferramentas = [
            buscar_imoveis_estruturado,
            buscar_imoveis_semantico,
            *(ferramentas_extras or []),
        ]

        # As ferramentas são executadas por nós (ver `_executar_ferramenta`),
        # não pelo SDK: a conversão automática do SDK é rígida e recusa,
        # por exemplo, `preco_max: 1000000` (inteiro) num parâmetro float.
        self._ferramentas = {
            ferramenta.__name__: validate_call(ferramenta)
            for ferramenta in ferramentas
        }

        self.config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=ferramentas,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True,
            ),
        )

        self._sessoes: dict[str, "genai.chats.Chat"] = {}

    def _obter_sessao(self, sessao_id: str):

        if sessao_id not in self._sessoes:

            self._sessoes[sessao_id] = self.client.chats.create(
                model=MODELO_PADRAO,
                config=self.config,
            )

        return self._sessoes[sessao_id]

    def responder(self, sessao_id: str, mensagem: str) -> str:

        chat = self._obter_sessao(sessao_id)

        resposta = chat.send_message(mensagem)

        for _ in range(MAX_RODADAS_FERRAMENTAS):

            chamadas = resposta.function_calls

            if not chamadas:
                break

            resposta = chat.send_message([
                types.Part.from_function_response(
                    name=chamada.name,
                    response=self._executar_ferramenta(chamada),
                )
                for chamada in chamadas
            ])

        return _texto(resposta) or RESPOSTA_SEM_TEXTO

    def _executar_ferramenta(self, chamada: types.FunctionCall) -> dict:
        """Executa a ferramenta pedida pelo modelo, convertendo os
        argumentos com o pydantic (aceita 1000000, 1000000.0 ou
        "1000000" num float). Erros voltam para o modelo como resposta da
        ferramenta, para ele corrigir ou explicar ao cliente."""

        ferramenta = self._ferramentas.get(chamada.name)

        if ferramenta is None:
            return {"erro": f"Ferramenta {chamada.name!r} não existe."}

        argumentos = dict(chamada.args or {})

        try:
            return {"resultado": ferramenta(**argumentos)}
        except ValidationError as erro:
            logger.warning("Argumentos inválidos em %s(%s): %s", chamada.name, argumentos, erro)
            return {"erro": f"Argumentos inválidos: {erro.errors(include_url=False)}"}
        except Exception as erro:
            logger.exception("Falha ao executar %s(%s)", chamada.name, argumentos)
            return {"erro": f"Falha ao executar a ferramenta: {erro}"}

    def adicionar_mensagem_agente(self, sessao_id: str, mensagem: str) -> None:
        """Insere no histórico uma mensagem enviada pela Bia fora de uma
        resposta (ex.: follow-up automático), para que ela faça parte do
        contexto quando o cliente voltar a responder."""

        historico = self._obter_sessao(sessao_id).get_history()
        parte = types.Part(text=mensagem)

        if historico and historico[-1].role == "model":
            historico[-1].parts = [*(historico[-1].parts or []), parte]
        else:
            historico.append(types.Content(role="model", parts=[parte]))

        self._sessoes[sessao_id] = self.client.chats.create(
            model=MODELO_PADRAO,
            config=self.config,
            history=historico,
        )

    def historico(self, sessao_id: str) -> list[dict]:

        if sessao_id not in self._sessoes:
            return []

        chat = self._sessoes[sessao_id]

        mensagens = [
            {
                "papel": conteudo.role,
                "texto": "\n\n".join(
                    parte.text
                    for parte in (conteudo.parts or [])
                    if parte.text
                ),
            }
            for conteudo in chat.get_history()
        ]

        # Chamadas/respostas de ferramentas não têm texto: ficam de fora.
        return [mensagem for mensagem in mensagens if mensagem["texto"]]

    def reiniciar(self, sessao_id: str) -> None:

        self._sessoes.pop(sessao_id, None)


def _texto(resposta) -> str:
    """Só as partes de texto da resposta (sem o aviso do SDK sobre partes
    que não são texto)."""

    partes = resposta.candidates[0].content.parts if resposta.candidates else []

    return "".join(parte.text for parte in (partes or []) if parte.text)
