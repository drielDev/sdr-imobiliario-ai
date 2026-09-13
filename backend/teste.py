from app.catalogo.models import FiltroImovel
from app.catalogo.service import CatalogoService


catalogo = CatalogoService()

filtro = FiltroImovel(
    finalidade="compra",
    tipo="apartamento",
    preco_max=700000,
    quartos_min=2
)

resultado = catalogo.buscar(filtro)

for imovel in resultado:
    print(imovel.titulo)
    print(imovel.preco)
    print()