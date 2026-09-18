from typing import Protocol

from app.qualificacao.models import Lead


class LeadRepository(Protocol):
    """Interface de persistência de leads. A implementação padrão do
    módulo guarda tudo em memória (adequado para a POC); outros módulos
    podem trocar por um repositório real (banco de dados, etc.) desde que
    sigam esta interface."""

    def salvar(self, lead: Lead) -> Lead:
        ...

    def obter(self, lead_id: str) -> Lead | None:
        ...

    def listar(self) -> list[Lead]:
        ...


class InMemoryLeadRepository:

    def __init__(self):
        self._leads: dict[str, Lead] = {}

    def salvar(self, lead: Lead) -> Lead:

        self._leads[lead.id] = lead

        return lead

    def obter(self, lead_id: str) -> Lead | None:

        return self._leads.get(lead_id)

    def listar(self) -> list[Lead]:

        return list(self._leads.values())
