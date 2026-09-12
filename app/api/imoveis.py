from fastapi import APIRouter, HTTPException

from app.catalogo.models import (
    FiltroImovel,
    Imovel
)
from app.catalogo.service import CatalogoService


router = APIRouter(
    prefix="/imoveis",
    tags=["Imóveis"]
)

service = CatalogoService()


@router.get("/", response_model=list[Imovel])
def listar_imoveis():

    return service.listar_imoveis()


@router.get(
    "/{imovel_id}",
    response_model=Imovel
)
def buscar_imovel(imovel_id: int):

    imovel = service.buscar_por_id(
        imovel_id
    )

    if not imovel:

        raise HTTPException(
            status_code=404,
            detail="Imóvel não encontrado"
        )

    return imovel


@router.post(
    "/buscar",
    response_model=list[Imovel]
)
def buscar_imoveis(
    filtros: FiltroImovel
):

    return service.buscar(filtros)
from fastapi import APIRouter, HTTPException

from app.catalogo.models import (
    FiltroImovel,
    Imovel
)
from app.catalogo.service import CatalogoService


router = APIRouter(
    prefix="/imoveis",
    tags=["Imóveis"]
)

service = CatalogoService()


@router.get("/", response_model=list[Imovel])
def listar_imoveis():

    return service.listar_imoveis()


@router.get(
    "/{imovel_id}",
    response_model=Imovel
)
def buscar_imovel(imovel_id: int):

    imovel = service.buscar_por_id(
        imovel_id
    )

    if not imovel:

        raise HTTPException(
            status_code=404,
            detail="Imóvel não encontrado"
        )

    return imovel


@router.post(
    "/buscar",
    response_model=list[Imovel]
)
def buscar_imoveis(
    filtros: FiltroImovel
):

    return service.buscar(filtros)