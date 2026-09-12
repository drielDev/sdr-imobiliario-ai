import json
from pathlib import Path

from app.catalogo.models import Imovel


class ImovelRepository:

    def __init__(self):
        caminho = (
            Path(__file__).resolve().parents[2]
            / "data"
            / "imoveis.json"
        )

        self.caminho = caminho

    def listar(self) -> list[Imovel]:

        with open(
            self.caminho,
            "r",
            encoding="utf-8"
        ) as arquivo:

            dados = json.load(arquivo)

        return [
            Imovel(**imovel)
            for imovel in dados
        ]

    def buscar_por_id(
        self,
        imovel_id: int
    ) -> Imovel | None:

        imoveis = self.listar()

        for imovel in imoveis:

            if imovel.id == imovel_id:
                return imovel

        return None
import json
from pathlib import Path

from app.catalogo.models import Imovel


class ImovelRepository:

    def __init__(self):
        caminho = (
            Path(__file__).resolve().parents[2]
            / "data"
            / "imoveis.json"
        )

        self.caminho = caminho

    def listar(self) -> list[Imovel]:

        with open(
            self.caminho,
            "r",
            encoding="utf-8"
        ) as arquivo:

            dados = json.load(arquivo)

        return [
            Imovel(**imovel)
            for imovel in dados
        ]

    def buscar_por_id(
        self,
        imovel_id: int
    ) -> Imovel | None:

        imoveis = self.listar()

        for imovel in imoveis:

            if imovel.id == imovel_id:
                return imovel

        return None