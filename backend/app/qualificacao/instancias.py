from app.qualificacao.agendamento import (
    AgendaService,
    InMemoryAgendaRepository,
    gerar_slots_padrao,
)
from app.qualificacao.followup import FollowUpService
from app.qualificacao.repository import InMemoryLeadRepository
from app.qualificacao.tempo import RelogioSistema

relogio = RelogioSistema()

lead_repository = InMemoryLeadRepository()

agenda_repository = InMemoryAgendaRepository(
    slots_iniciais=gerar_slots_padrao(relogio)
)
agenda_service = AgendaService(agenda_repository, relogio)

followup_service = FollowUpService(lead_repository, relogio)
