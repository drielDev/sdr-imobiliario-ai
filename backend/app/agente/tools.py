from typing import Optional

from app.catalogo.instancias import rag, service
from app.catalogo.models import FiltroImovel

LIMITE_RESULTADOS_ESTRUTURADO = 8


def _imovel_para_dict(imovel) -> dict:

    return {
        "id": imovel.id,
        "titulo": imovel.titulo,
        "tipo": imovel.tipo,
        "finalidade": imovel.finalidade,
        "preco": imovel.preco,
        "cidade": imovel.cidade,
        "bairro": imovel.bairro,
        "quartos": imovel.quartos,
        "banheiros": imovel.banheiros,
        "vagas": imovel.vagas,
        "area_m2": imovel.area_m2,
        "descricao": imovel.descricao,
    }


def buscar_imoveis_estruturado(
    finalidade: Optional[str] = None,
    tipo: Optional[str] = None,
    cidade: Optional[str] = None,
    bairro: Optional[str] = None,
    preco_min: Optional[float] = None,
    preco_max: Optional[float] = None,
    quartos_min: Optional[int] = None,
    vagas_min: Optional[int] = None,
) -> list[dict]:
    """Busca imóveis por critérios exatos: finalidade (compra/aluguel), tipo,
    cidade, bairro, faixa de preço, quartos e vagas mínimos. Use quando o
    cliente já deu esses dados na conversa; parâmetros não informados ficam
    de fora do filtro."""

    filtros = FiltroImovel(
        finalidade=finalidade,
        tipo=tipo,
        cidade=cidade,
        bairro=bairro,
        preco_min=preco_min,
        preco_max=preco_max,
        quartos_min=quartos_min,
        vagas_min=vagas_min,
    )

    resultado = service.buscar(filtros)

    return [
        _imovel_para_dict(imovel)
        for imovel in resultado[:LIMITE_RESULTADOS_ESTRUTURADO]
    ]


def buscar_imoveis_semantico(
    consulta: str,
    finalidade: Optional[str] = None,
    tipo: Optional[str] = None,
    cidade: Optional[str] = None,
    bairro: Optional[str] = None,
    preco_min: Optional[float] = None,
    preco_max: Optional[float] = None,
    quartos_min: Optional[int] = None,
    vagas_min: Optional[int] = None,
    limite: int = 5,
) -> list[dict]:
    """Busca imóveis por similaridade de texto, pra pedidos vagos ou
    descritivos tipo "algo moderno para investir" ou "casa grande para
    família". Pode combinar a descrição livre com filtros objetivos já
    conhecidos. Retorna os imóveis mais relevantes, já rankeados."""

    tem_filtro = any(
        valor is not None
        for valor in (
            finalidade,
            tipo,
            cidade,
            bairro,
            preco_min,
            preco_max,
            quartos_min,
            vagas_min,
        )
    )

    filtros = (
        FiltroImovel(
            finalidade=finalidade,
            tipo=tipo,
            cidade=cidade,
            bairro=bairro,
            preco_min=preco_min,
            preco_max=preco_max,
            quartos_min=quartos_min,
            vagas_min=vagas_min,
        )
        if tem_filtro
        else None
    )

    documentos = rag.buscar_avancado(
        consulta=consulta,
        limite=limite,
        filtros=filtros,
    )

    return [
        {
            "id": documento.metadata.get("imovel_id"),
            "titulo": documento.metadata.get("titulo"),
            "tipo": documento.metadata.get("tipo"),
            "finalidade": documento.metadata.get("finalidade"),
            "preco": documento.metadata.get("preco"),
            "cidade": documento.metadata.get("cidade"),
            "bairro": documento.metadata.get("bairro"),
            "quartos": documento.metadata.get("quartos"),
            "vagas": documento.metadata.get("vagas"),
            "conteudo": documento.page_content,
        }
        for documento in documentos
    ]
