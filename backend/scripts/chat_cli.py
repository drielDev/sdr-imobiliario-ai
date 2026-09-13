import sys
import uuid

import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = "http://127.0.0.1:8000"


def main():

    sessao_id = str(uuid.uuid4())

    print("Chat com a Bia (SDR). Digite 'sair' para encerrar.\n")

    while True:

        mensagem = input("Você: ").strip()

        if mensagem.lower() in ("sair", "exit", "quit"):
            print("Encerrado.")
            break

        if not mensagem:
            continue

        try:
            resposta = requests.post(
                f"{BASE_URL}/chat/",
                json={
                    "sessao_id": sessao_id,
                    "mensagem": mensagem,
                },
                timeout=60,
            )
        except requests.exceptions.ConnectionError:
            print("Erro: não conectou na API. Ela está rodando em"
                  f" {BASE_URL}?")
            continue

        if resposta.status_code != 200:
            print(f"Erro ({resposta.status_code}): {resposta.text}")
            continue

        dados = resposta.json()
        print(f"\nBia: {dados['resposta']}\n")


if __name__ == "__main__":
    main()
