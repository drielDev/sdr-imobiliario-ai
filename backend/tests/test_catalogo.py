from app.catalogo.models import FiltroImovel
from app.catalogo.service import CatalogoService


service = CatalogoService()


def test_listar_imoveis():

    resultado = service.listar_imoveis()

    assert len(resultado) > 0


def test_busca_por_preco():

    filtro = FiltroImovel(
        preco_max=700000
    )

    resultado = service.buscar(filtro)

    assert len(resultado) > 0

    for imovel in resultado:

        assert imovel.preco <= 700000


def test_busca_por_quartos():

    filtro = FiltroImovel(
        quartos_min=3
    )

    resultado = service.buscar(filtro)

    for imovel in resultado:

        assert imovel.quartos >= 3


def test_busca_compra():

    filtro = FiltroImovel(
        finalidade="compra"
    )

    resultado = service.buscar(filtro)

    for imovel in resultado:

        assert imovel.finalidade == "compra"
