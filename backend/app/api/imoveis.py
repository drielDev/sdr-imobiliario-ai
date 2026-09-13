from fastapi import APIRouter, HTTPException

from app.catalogo.instancias import rag, service
from app.catalogo.models import (
    ConsultaRAG,
    FiltroImovel,
    Imovel
)


router = APIRouter(
    prefix="/imoveis",
    tags=["Imóveis"]
)


@router.get("/", response_model=list[Imovel])
def listar_imoveis():

    return service.listar_imoveis()


@router.get(
    "/{imovel_id}",
    response_model=Imovel
)
def buscar_imovel(imovel_id: int):

    imovel = service.buscar_por_id(imovel_id)

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


@router.post("/rag")
def buscar_rag(
    dados: ConsultaRAG
):

    documentos = rag.buscar_avancado(
        consulta=dados.consulta,
        limite=dados.limite,
        filtros=dados.filtros
    )

    resultado = []

    for documento in documentos:

        resultado.append(
            {
                "imovel_id": documento.metadata.get("imovel_id"),
                "titulo": documento.metadata.get("titulo"),
                "finalidade": documento.metadata.get("finalidade"),
                "quartos": documento.metadata.get("quartos"),
                "preco": documento.metadata.get("preco"),
                "conteudo": documento.page_content,
            }
        )

    return {
        "consulta": dados.consulta,
        "quantidade": len(resultado),
        "resultados": resultado,
    }