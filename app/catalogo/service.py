from app.catalogo.models import FiltroImovel, Imovel
from app.catalogo.repository import ImovelRepository


class CatalogoService:

    def __init__(self):
        self.repository = ImovelRepository()

    def listar_imoveis(self) -> list[Imovel]:
        return self.repository.listar()

    def buscar_por_id(
        self,
        imovel_id: int
    ) -> Imovel | None:

        return self.repository.buscar_por_id(
            imovel_id
        )

    def buscar(
        self,
        filtros: FiltroImovel
    ) -> list[Imovel]:

        imoveis = self.repository.listar()

        resultado = []

        for imovel in imoveis:

            if not imovel.disponivel:
                continue

            if (
                filtros.finalidade
                and imovel.finalidade.lower()
                != filtros.finalidade.lower()
            ):
                continue

            if (
                filtros.tipo
                and imovel.tipo.lower()
                != filtros.tipo.lower()
            ):
                continue

            if (
                filtros.cidade
                and filtros.cidade.lower()
                not in imovel.cidade.lower()
            ):
                continue

            if (
                filtros.bairro
                and filtros.bairro.lower()
                not in imovel.bairro.lower()
            ):
                continue

            if (
                filtros.preco_min is not None
                and imovel.preco < filtros.preco_min
            ):
                continue

            if (
                filtros.preco_max is not None
                and imovel.preco > filtros.preco_max
            ):
                continue

            if (
                filtros.quartos_min is not None
                and imovel.quartos < filtros.quartos_min
            ):
                continue

            if (
                filtros.vagas_min is not None
                and imovel.vagas < filtros.vagas_min
            ):
                continue

            resultado.append(imovel)

        return resultado
from app.catalogo.models import FiltroImovel, Imovel
from app.catalogo.repository import ImovelRepository


class CatalogoService:

    def __init__(self):
        self.repository = ImovelRepository()

    def listar_imoveis(self) -> list[Imovel]:
        return self.repository.listar()

    def buscar_por_id(
        self,
        imovel_id: int
    ) -> Imovel | None:

        return self.repository.buscar_por_id(
            imovel_id
        )

    def buscar(
        self,
        filtros: FiltroImovel
    ) -> list[Imovel]:

        imoveis = self.repository.listar()

        resultado = []

        for imovel in imoveis:

            if not imovel.disponivel:
                continue

            if (
                filtros.finalidade
                and imovel.finalidade.lower()
                != filtros.finalidade.lower()
            ):
                continue

            if (
                filtros.tipo
                and imovel.tipo.lower()
                != filtros.tipo.lower()
            ):
                continue

            if (
                filtros.cidade
                and filtros.cidade.lower()
                not in imovel.cidade.lower()
            ):
                continue

            if (
                filtros.bairro
                and filtros.bairro.lower()
                not in imovel.bairro.lower()
            ):
                continue

            if (
                filtros.preco_min is not None
                and imovel.preco < filtros.preco_min
            ):
                continue

            if (
                filtros.preco_max is not None
                and imovel.preco > filtros.preco_max
            ):
                continue

            if (
                filtros.quartos_min is not None
                and imovel.quartos < filtros.quartos_min
            ):
                continue

            if (
                filtros.vagas_min is not None
                and imovel.vagas < filtros.vagas_min
            ):
                continue

            resultado.append(imovel)

        return resultado