import os

from google import genai
from google.genai import types

from app.agente.prompts import SYSTEM_PROMPT
from app.agente.tools import buscar_imoveis_estruturado, buscar_imoveis_semantico

MODELO_PADRAO = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


class AgenteSDR:

    def __init__(self):

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY não configurada. Defina a variável de "
                "ambiente (ou crie um arquivo .env) com sua chave da API "
                "do Gemini."
            )

        self.client = genai.Client(api_key=api_key)

        self.config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[
                buscar_imoveis_estruturado,
                buscar_imoveis_semantico,
            ],
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

        return resposta.text

    def historico(self, sessao_id: str) -> list[dict]:

        if sessao_id not in self._sessoes:
            return []

        chat = self._sessoes[sessao_id]

        return [
            {
                "papel": conteudo.role,
                "texto": "".join(
                    parte.text or ""
                    for parte in (conteudo.parts or [])
                ),
            }
            for conteudo in chat.get_history()
        ]

    def reiniciar(self, sessao_id: str) -> None:

        self._sessoes.pop(sessao_id, None)
