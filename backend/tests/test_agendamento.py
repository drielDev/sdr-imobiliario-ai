from datetime import datetime, timedelta

import pytest

from app.qualificacao.agendamento import (
    AgendaService,
    ConflitoDeHorarioError,
    InMemoryAgendaRepository,
    ResponsavelTipo,
    SlotDisponibilidade,
    SlotIndisponivelError,
    TipoAgendamento,
    gerar_slots_padrao,
    tipo_sugerido_para,
)
from app.qualificacao.models import Intencao, Lead


class RelogioFalso:

    def __init__(self, inicio: datetime):
        self._agora = inicio

    def agora(self) -> datetime:
        return self._agora


def _lead(intencao=Intencao.COMPRA, imovel_interesse_id=None) -> Lead:

    agora = datetime(2026, 1, 1, 9, 0)

    return Lead(
        id="lead-1",
        canal="whatsapp",
        contato="123",
        intencao=intencao,
        imovel_interesse_id=imovel_interesse_id,
        criado_em=agora,
        atualizado_em=agora,
        ultima_interacao_em=agora,
    )


def _slot(id_, responsavel=ResponsavelTipo.CORRETOR, inicio=None) -> SlotDisponibilidade:

    inicio = inicio or datetime(2026, 1, 5, 10, 0)

    return SlotDisponibilidade(
        id=id_,
        inicio=inicio,
        fim=inicio + timedelta(hours=1),
        responsavel=responsavel,
    )


def _service(slots):

    relogio = RelogioFalso(datetime(2026, 1, 1, 9, 0))
    repo = InMemoryAgendaRepository(slots_iniciais=slots)

    return AgendaService(repo, relogio), repo


def test_roteamento_investimento_vai_para_especialista():

    lead = _lead(intencao=Intencao.INVESTIMENTO)

    assert tipo_sugerido_para(lead) == TipoAgendamento.REUNIAO_ESPECIALISTA


def test_roteamento_com_imovel_de_interesse_sugere_visita():

    lead = _lead(imovel_interesse_id=7)

    assert tipo_sugerido_para(lead) == TipoAgendamento.VISITA_IMOVEL


def test_agendar_ocupa_slot_e_evita_conflito():

    slot = _slot("slot-1")
    service, _ = _service([slot])
    lead = _lead()

    agendamento = service.agendar(lead, slot_id="slot-1", tipo=TipoAgendamento.REUNIAO_CORRETOR)

    assert agendamento.responsavel == ResponsavelTipo.CORRETOR

    with pytest.raises(ConflitoDeHorarioError):
        service.agendar(_lead(), slot_id="slot-1", tipo=TipoAgendamento.REUNIAO_CORRETOR)


def test_lead_investimento_forca_slot_de_especialista():

    slot_corretor = _slot("slot-c", responsavel=ResponsavelTipo.CORRETOR)
    service, _ = _service([slot_corretor])
    lead = _lead(intencao=Intencao.INVESTIMENTO)

    with pytest.raises(SlotIndisponivelError):
        service.agendar(lead, slot_id="slot-c")


def test_reagendar_libera_slot_antigo_e_ocupa_novo():

    slot1 = _slot("slot-1", inicio=datetime(2026, 1, 5, 10, 0))
    slot2 = _slot("slot-2", inicio=datetime(2026, 1, 6, 10, 0))
    service, repo = _service([slot1, slot2])
    lead = _lead()

    agendamento = service.agendar(lead, slot_id="slot-1", tipo=TipoAgendamento.REUNIAO_CORRETOR)
    reagendado = service.reagendar(agendamento.id, "slot-2")

    assert reagendado.slot_id == "slot-2"
    assert repo.obter_slot("slot-1").ocupado is False
    assert repo.obter_slot("slot-2").ocupado is True


def test_cancelar_libera_slot():

    slot = _slot("slot-1")
    service, repo = _service([slot])
    lead = _lead()

    agendamento = service.agendar(lead, slot_id="slot-1", tipo=TipoAgendamento.REUNIAO_CORRETOR)
    service.cancelar(agendamento.id)

    assert repo.obter_slot("slot-1").ocupado is False


def test_listar_slots_disponiveis_ignora_ocupados_e_passados():

    passado = _slot("slot-passado", inicio=datetime(2025, 1, 1, 10, 0))
    futuro = _slot("slot-futuro", inicio=datetime(2026, 2, 1, 10, 0))
    service, _ = _service([passado, futuro])

    disponiveis = service.listar_slots_disponiveis()

    assert [slot.id for slot in disponiveis] == ["slot-futuro"]


def test_gerar_slots_padrao_cria_slots_para_corretor_e_especialista_em_dias_uteis():

    relogio = RelogioFalso(datetime(2026, 1, 5, 8, 0))
    slots = gerar_slots_padrao(relogio, dias_uteis=3)

    responsaveis = {slot.responsavel for slot in slots}

    assert responsaveis == {ResponsavelTipo.CORRETOR, ResponsavelTipo.ESPECIALISTA}
    assert all(slot.inicio.weekday() < 5 for slot in slots)
