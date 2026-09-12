from pydantic import BaseModel
from typing import Optional


class Imovel(BaseModel):
    id: int
    titulo: str
    tipo: str
    finalidade: str
    preco: float
    cidade: str
    bairro: str
    quartos: int
    banheiros: int
    vagas: int
    area_m2: float
    descricao: str
    disponivel: bool


class FiltroImovel(BaseModel):
    finalidade: Optional[str] = None
    tipo: Optional[str] = None
    cidade: Optional[str] = None
    bairro: Optional[str] = None

    preco_min: Optional[float] = None
    preco_max: Optional[float] = None

    quartos_min: Optional[int] = None
    vagas_min: Optional[int] = None


class ConsultaRAG(BaseModel):
    consulta: str
    limite: int = 5
    filtros: Optional[FiltroImovel] = None
from pydantic import BaseModel
from typing import Optional


class Imovel(BaseModel):
    id: int
    titulo: str
    tipo: str
    finalidade: str
    preco: float
    cidade: str
    bairro: str
    quartos: int
    banheiros: int
    vagas: int
    area_m2: float
    descricao: str
    disponivel: bool


class FiltroImovel(BaseModel):
    finalidade: Optional[str] = None
    tipo: Optional[str] = None
    cidade: Optional[str] = None
    bairro: Optional[str] = None

    preco_min: Optional[float] = None
    preco_max: Optional[float] = None

    quartos_min: Optional[int] = None
    vagas_min: Optional[int] = None
    

class ConsultaRAG(BaseModel):
    consulta: str
    limite: int = 5