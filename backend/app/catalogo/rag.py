from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import re
import unicodedata

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

try:
    from sentence_transformers import CrossEncoder
except ImportError:  # pragma: no cover
    CrossEncoder = None

from app.catalogo.models import FiltroImovel
from app.catalogo.repository import ImovelRepository
from app.catalogo.service import CatalogoService


@dataclass(frozen=True)
class ResultadoRAG:
    documento: Document
    score_total: float
    score_vetorial: float
    score_lexical: float


class ImovelRAG:

    def __init__(self):

        base_dir = Path(__file__).resolve().parents[2]

        self.db_path = base_dir / "chroma_db"
        self.repository = ImovelRepository()
        self.service = CatalogoService()

        self.embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-m3",
            encode_kwargs={
                "normalize_embeddings": True
            }
        )

        self.vector_store = Chroma(
            collection_name="imoveis",
            embedding_function=self.embeddings,
            persist_directory=str(self.db_path)
        )

        self.reranker = None
        if CrossEncoder is not None:
            try:
                self.reranker = CrossEncoder(
                    "cross-encoder/ms-marco-MiniLM-L-6-v2"
                )
            except Exception:
                self.reranker = None

    def _normalizar_texto(self, texto: str) -> str:
        texto = texto.lower().strip()
        texto = unicodedata.normalize("NFD", texto)
        texto = "".join(
            caractere
            for caractere in texto
            if unicodedata.category(caractere) != "Mn"
        )
        texto = re.sub(r"[^\w\s]", " ", texto)
        texto = re.sub(r"\s+", " ", texto)
        return texto.strip()

    def _montar_texto_documento(self, imovel) -> str:

        return (
            f"Titulo: {imovel.titulo}. "
            f"Tipo: {imovel.tipo}. "
            f"Finalidade: {imovel.finalidade}. "
            f"Cidade: {imovel.cidade}. "
            f"Bairro: {imovel.bairro}. "
            f"Preco: {imovel.preco}. "
            f"Quartos: {imovel.quartos}. "
            f"Banheiros: {imovel.banheiros}. "
            f"Vagas: {imovel.vagas}. "
            f"Area: {imovel.area_m2} m2. "
            f"Descricao: {imovel.descricao}. "
            f"Ideal para {imovel.tipo} em {imovel.bairro}, "
            f"com {imovel.quartos} quartos e {imovel.vagas} vagas."
        )

    def _documento_aceita_filtros(
        self,
        documento: Document,
        filtros: FiltroImovel
    ) -> bool:

        if filtros.finalidade:
            if documento.metadata.get("finalidade", "").lower() != filtros.finalidade.lower():
                return False

        if filtros.tipo:
            if documento.metadata.get("tipo", "").lower() != filtros.tipo.lower():
                return False

        if filtros.cidade:
            if filtros.cidade.lower() not in documento.metadata.get("cidade", "").lower():
                return False

        if filtros.bairro:
            if filtros.bairro.lower() not in documento.metadata.get("bairro", "").lower():
                return False

        if filtros.preco_min is not None:
            if float(documento.metadata.get("preco", 0)) < filtros.preco_min:
                return False

        if filtros.preco_max is not None:
            if float(documento.metadata.get("preco", 0)) > filtros.preco_max:
                return False

        if filtros.quartos_min is not None:
            if int(documento.metadata.get("quartos", 0)) < filtros.quartos_min:
                return False

        if filtros.vagas_min is not None:
            if int(documento.metadata.get("vagas", 0)) < filtros.vagas_min:
                return False

        return True

    def _deduzir_filtros_da_consulta(self, consulta: str) -> FiltroImovel | None:

        consulta_norm = self._normalizar_texto(consulta)
        tokens = set(consulta_norm.split())

        if (
            "familia" in tokens
            and ("quartos" in tokens or "quarto" in tokens)
            and ("muitos" in tokens or "grande" in tokens or "espacioso" in tokens or "espaciosa" in tokens)
        ):
            return FiltroImovel(quartos_min=3)

        return None

    def gerar_documentos(self):

        imoveis = self.repository.listar()
        documentos = []

        for imovel in imoveis:

            texto = self._montar_texto_documento(imovel)

            documento = Document(
                page_content=texto,
                metadata={
                    "imovel_id": imovel.id,
                    "titulo": imovel.titulo,
                    "tipo": imovel.tipo,
                    "cidade": imovel.cidade,
                    "bairro": imovel.bairro,
                    "finalidade": imovel.finalidade,
                    "quartos": imovel.quartos,
                    "vagas": imovel.vagas,
                    "preco": imovel.preco,
                    "disponivel": imovel.disponivel,
                    "texto_normalizado": self._normalizar_texto(texto),
                }
            )

            documentos.append(documento)

        return documentos

    def indexar(self):

        documentos = self.gerar_documentos()

        ids = [
            f"imovel-{doc.metadata['imovel_id']}"
            for doc in documentos
        ]

        self.vector_store.add_documents(
            documentos,
            ids=ids
        )

    def _pontuar_lexicamente(self, consulta: str, documento: Document) -> float:

        consulta_norm = self._normalizar_texto(consulta)
        conteudo = documento.metadata.get("texto_normalizado", "")

        consulta_tokens = set(consulta_norm.split())
        if not consulta_tokens:
            return 0.0

        conteudo_tokens = set(conteudo.split())
        intersecao = consulta_tokens & conteudo_tokens

        score = len(intersecao) / len(consulta_tokens)

        quartos = documento.metadata.get("quartos", 0)

        if "quarto" in consulta_tokens or "quartos" in consulta_tokens:
            if quartos >= 4:
                score += 0.35
            elif quartos >= 3:
                score += 0.25
            elif quartos == 2:
                score += 0.10
            else:
                score -= 0.10

        if "familia" in consulta_tokens:
            if quartos >= 4:
                score += 0.95
            elif quartos >= 3:
                score += 0.15
            else:
                score -= 0.90

            if documento.metadata.get("tipo") == "casa":
                score += 0.55

        if "muitos" in consulta_tokens and "quartos" in consulta_tokens:
            if quartos >= 4:
                score += 1.15
            elif quartos >= 3:
                score += 0.10
            else:
                score -= 1.00

        finalidade = documento.metadata.get("finalidade")

        if "aluguel" in consulta_tokens or "locacao" in consulta_tokens or "locação" in consulta:
            if finalidade == "aluguel":
                score += 0.30
            else:
                score -= 0.10

        if "compra" in consulta_tokens:
            if finalidade == "compra":
                score += 0.30
            else:
                score -= 0.10

        if "barato" in consulta_tokens or "economico" in consulta_tokens or "econômico" in consulta:
            preco = float(documento.metadata.get("preco", 0))
            if preco <= 500000:
                score += 0.15

        if "luxo" in consulta_tokens or "alto padrao" in consulta or "alto padrão" in consulta:
            preco = float(documento.metadata.get("preco", 0))
            if preco >= 900000:
                score += 0.15

        return score

    def _pontuar_reranker(self, consulta: str, documento: Document) -> float:

        if self.reranker is None:
            return 0.0

        try:
            resultado = self.reranker.predict([
                [consulta, documento.page_content]
            ])
            return float(resultado[0])
        except Exception:
            return 0.0

    def buscar(
        self,
        consulta: str,
        limite: int = 5,
        filtros: FiltroImovel | None = None
    ):

        consulta_normalizada = self._normalizar_texto(consulta)

        if filtros is None:
            filtros = self._deduzir_filtros_da_consulta(consulta)

        candidatos = []
        for documento in self.gerar_documentos():

            if filtros and not self._documento_aceita_filtros(documento, filtros):
                continue

            candidatos.append(documento)

        if not candidatos:
            return []

        consulta_embedding = self.embeddings.embed_query(consulta_normalizada)
        documentos_embeddings = self.embeddings.embed_documents(
            [doc.page_content for doc in candidatos]
        )

        resultados = []

        for documento, embedding_documento in zip(candidatos, documentos_embeddings):

            score_vetorial = sum(
                valor_consulta * valor_documento
                for valor_consulta, valor_documento in zip(
                    consulta_embedding,
                    embedding_documento
                )
            )

            score_lexical = self._pontuar_lexicamente(consulta, documento)
            score_reranker = self._pontuar_reranker(consulta, documento)

            if self.reranker is not None:
                score_total = (
                    0.45 * score_vetorial
                    + 0.25 * score_lexical
                    + 0.30 * score_reranker
                )
            else:
                score_total = (0.7 * score_vetorial) + (0.3 * score_lexical)

            resultados.append(
                ResultadoRAG(
                    documento=documento,
                    score_total=score_total,
                    score_vetorial=score_vetorial,
                    score_lexical=score_lexical + score_reranker,
                )
            )

        resultados.sort(key=lambda item: item.score_total, reverse=True)

        return [
            item.documento
            for item in resultados[:limite]
        ]

    def buscar_avancado(
        self,
        consulta: str,
        limite: int = 5,
        filtros: FiltroImovel | None = None
    ):

        if filtros is not None:
            return self.buscar(
                consulta=consulta,
                limite=limite,
                filtros=filtros
            )

        return self.buscar(
            consulta=consulta,
            limite=limite
        )