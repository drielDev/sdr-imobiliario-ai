import json

from app.catalogo.rag import ImovelRAG


rag = ImovelRAG()

resultados = rag.buscar(
    "imovel barato para alugar com boa localização",
    limite=3
)

saida = {
    "consulta": "imovel barato para alugar com boa localização",
    "quantidade": len(resultados),
    "resultados": [
        {
            "imovel_id": resultado.metadata.get("imovel_id"),
            "titulo": resultado.metadata.get("titulo"),
            "finalidade": resultado.metadata.get("finalidade"),
            "quartos": resultado.metadata.get("quartos"),
            "preco": resultado.metadata.get("preco"),
            "conteudo": resultado.page_content,
        }
        for resultado in resultados
    ]
}

print(json.dumps(saida, ensure_ascii=False, indent=2))