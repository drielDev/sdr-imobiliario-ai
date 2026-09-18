import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Protocol

from pydantic import BaseModel

from app.qualificacao.config import (
    DIAS_UTEIS_GERADOS,
    DURACAO_SLOT_MINUTOS,
    HORARIO_FIM,
    HORARIO_INICIO,
)
from app.qualificacao.models import Intencao, Lead
from app.qualificacao.tempo import Relogio, RelogioSistema

logger = logging.getLogger("qualificacao")

_RELOGIO_PADRAO = RelogioSistema()


class TipoAgendamento(str, Enum):
    VISITA_IMOVEL = "visita_imovel"
    REUNIAO_CORRETOR = "reuniao_corretor"
    REUNIAO_ESPECIALISTA = "reuniao_especialista"


class ResponsavelTipo(str, Enum):
    CORRETOR = "corretor"
    ESPECIALISTA = "especialista"


class StatusAgendamento(str, Enum):
    CONFIRMADO = "confirmado"
    CANCELADO = "cancelado"
    REAGENDADO = "reagendado"


_RESPONSAVEL_POR_TIPO: dict[TipoAgendamento, ResponsavelTipo] = {
    TipoAgendamento.VISITA_IMOVEL: ResponsavelTipo.CORRETOR,
    TipoAgendamento.REUNIAO_CORRETOR: ResponsavelTipo.CORRETOR,
    TipoAgendamento.REUNIAO_ESPECIALISTA: ResponsavelTipo.ESPECIALISTA,
}


class ConflitoDeHorarioError(Exception):
    pass


class SlotIndisponivelError(Exception):
    pass


class AgendamentoNaoEncontradoError(Exception):
    pass


class SlotDisponibilidade(BaseModel):
    id: str
    inicio: datetime
    fim: datetime
    responsavel: ResponsavelTipo
    ocupado: bool = False


class Agendamento(BaseModel):
    id: str
    lead_id: str
    slot_id: str
    tipo: TipoAgendamento
    responsavel: ResponsavelTipo
    inicio: datetime
    fim: datetime
    imovel_id: int | None = None
    status: StatusAgendamento = StatusAgendamento.CONFIRMADO
    criado_em: datetime


def tipo_sugerido_para(lead: Lead) -> TipoAgendamento:
    """Roteamento padrão: lead de investimento vai para o especialista;
    lead com um imóvel específico de interesse vai para visita; os
    demais vão para reunião com corretor. Quem chama pode sobrescrever
    passando `tipo` explicitamente em `AgendaService.agendar`."""

    if lead.intencao == Intencao.INVESTIMENTO:
        return TipoAgendamento.REUNIAO_ESPECIALISTA

    if lead.imovel_interesse_id is not None:
        return TipoAgendamento.VISITA_IMOVEL

    return TipoAgendamento.REUNIAO_CORRETOR


def _proximos_dias_uteis(inicio: datetime, quantidade: int) -> list[datetime]:

    dias: list[datetime] = []
    cursor = inicio

    while len(dias) < quantidade:

        cursor = cursor + timedelta(days=1)

        if cursor.weekday() < 5:
            dias.append(cursor)

    return dias


def gerar_slots_padrao(
    relogio: Relogio = _RELOGIO_PADRAO,
    dias_uteis: int = DIAS_UTEIS_GERADOS,
) -> list[SlotDisponibilidade]:
    """Gera a agenda simulada: slots de 1h (configurável), em dias úteis,
    dentro do horário comercial configurado, um conjunto para corretores e
    outro para especialistas."""

    agora = relogio.agora()
    dias = _proximos_dias_uteis(agora, dias_uteis)

    slots: list[SlotDisponibilidade] = []
    contador = 0

    for dia in dias:

        hora = HORARIO_INICIO

        while hora < HORARIO_FIM:

            inicio = dia.replace(
                hour=hora,
                minute=0,
                second=0,
                microsecond=0,
            )
            fim = inicio + timedelta(minutes=DURACAO_SLOT_MINUTOS)

            for responsavel in ResponsavelTipo:

                contador += 1

                slots.append(
                    SlotDisponibilidade(
                        id=f"slot-{responsavel.value}-{contador}",
                        inicio=inicio,
                        fim=fim,
                        responsavel=responsavel,
                    )
                )

            hora += DURACAO_SLOT_MINUTOS // 60

    return slots


class AgendaRepository(Protocol):

    def listar_slots(self) -> list[SlotDisponibilidade]:
        ...

    def obter_slot(self, slot_id: str) -> SlotDisponibilidade | None:
        ...

    def salvar_slot(self, slot: SlotDisponibilidade) -> SlotDisponibilidade:
        ...

    def listar_agendamentos(self) -> list[Agendamento]:
        ...

    def obter_agendamento(self, agendamento_id: str) -> Agendamento | None:
        ...

    def salvar_agendamento(self, agendamento: Agendamento) -> Agendamento:
        ...


class InMemoryAgendaRepository:

    def __init__(
        self,
        slots_iniciais: list[SlotDisponibilidade] | None = None,
    ):
        self._slots = {
            slot.id: slot
            for slot in (slots_iniciais or [])
        }
        self._agendamentos: dict[str, Agendamento] = {}

    def listar_slots(self) -> list[SlotDisponibilidade]:

        return list(self._slots.values())

    def obter_slot(self, slot_id: str) -> SlotDisponibilidade | None:

        return self._slots.get(slot_id)

    def salvar_slot(self, slot: SlotDisponibilidade) -> SlotDisponibilidade:

        self._slots[slot.id] = slot

        return slot

    def listar_agendamentos(self) -> list[Agendamento]:

        return list(self._agendamentos.values())

    def obter_agendamento(self, agendamento_id: str) -> Agendamento | None:

        return self._agendamentos.get(agendamento_id)

    def salvar_agendamento(self, agendamento: Agendamento) -> Agendamento:

        self._agendamentos[agendamento.id] = agendamento

        return agendamento


class AgendaService:

    def __init__(
        self,
        repository: AgendaRepository,
        relogio: Relogio = _RELOGIO_PADRAO,
    ):
        self.repository = repository
        self.relogio = relogio

    def listar_slots_disponiveis(
        self,
        tipo: TipoAgendamento | None = None,
        a_partir_de: datetime | None = None,
    ) -> list[SlotDisponibilidade]:

        responsavel = _RESPONSAVEL_POR_TIPO[tipo] if tipo else None
        limite = a_partir_de or self.relogio.agora()

        disponiveis = [
            slot
            for slot in self.repository.listar_slots()
            if not slot.ocupado
            and slot.inicio >= limite
            and (responsavel is None or slot.responsavel == responsavel)
        ]

        return sorted(disponiveis, key=lambda slot: slot.inicio)

    def agendar(
        self,
        lead: Lead,
        slot_id: str,
        tipo: TipoAgendamento | None = None,
        imovel_id: int | None = None,
    ) -> Agendamento:

        tipo_escolhido = tipo or tipo_sugerido_para(lead)

        if (
            lead.intencao == Intencao.INVESTIMENTO
            and tipo_escolhido != TipoAgendamento.REUNIAO_ESPECIALISTA
        ):
            logger.info(
                "Lead %s é de investimento: roteando %s -> reuniao_especialista",
                lead.id,
                tipo_escolhido.value,
            )
            tipo_escolhido = TipoAgendamento.REUNIAO_ESPECIALISTA

        slot = self.repository.obter_slot(slot_id)

        if slot is None:
            raise SlotIndisponivelError(f"Slot {slot_id!r} não existe.")

        if slot.ocupado:
            raise ConflitoDeHorarioError(f"Slot {slot_id!r} já está ocupado.")

        responsavel_esperado = _RESPONSAVEL_POR_TIPO[tipo_escolhido]

        if slot.responsavel != responsavel_esperado:
            raise SlotIndisponivelError(
                f"Slot {slot_id!r} é de {slot.responsavel.value}, mas "
                f"esse agendamento precisa de {responsavel_esperado.value}."
            )

        slot.ocupado = True
        self.repository.salvar_slot(slot)

        agendamento = Agendamento(
            id=f"agenda-{lead.id}-{slot.id}",
            lead_id=lead.id,
            slot_id=slot.id,
            tipo=tipo_escolhido,
            responsavel=slot.responsavel,
            inicio=slot.inicio,
            fim=slot.fim,
            imovel_id=imovel_id,
            criado_em=self.relogio.agora(),
        )

        self.repository.salvar_agendamento(agendamento)

        logger.info(
            "Agendamento %s criado para lead %s (%s, %s)",
            agendamento.id,
            lead.id,
            tipo_escolhido.value,
            slot.inicio.isoformat(),
        )

        return agendamento

    def reagendar(
        self,
        agendamento_id: str,
        novo_slot_id: str,
    ) -> Agendamento:

        agendamento = self.repository.obter_agendamento(agendamento_id)

        if agendamento is None:
            raise AgendamentoNaoEncontradoError(
                f"Agendamento {agendamento_id!r} não encontrado."
            )

        novo_slot = self.repository.obter_slot(novo_slot_id)

        if novo_slot is None:
            raise SlotIndisponivelError(f"Slot {novo_slot_id!r} não existe.")

        if novo_slot.ocupado:
            raise ConflitoDeHorarioError(
                f"Slot {novo_slot_id!r} já está ocupado."
            )

        if novo_slot.responsavel != agendamento.responsavel:
            raise SlotIndisponivelError(
                "O novo slot precisa ser do mesmo responsável do "
                "agendamento original."
            )

        slot_antigo = self.repository.obter_slot(agendamento.slot_id)

        if slot_antigo is not None:
            slot_antigo.ocupado = False
            self.repository.salvar_slot(slot_antigo)

        novo_slot.ocupado = True
        self.repository.salvar_slot(novo_slot)

        agendamento.slot_id = novo_slot.id
        agendamento.inicio = novo_slot.inicio
        agendamento.fim = novo_slot.fim
        agendamento.status = StatusAgendamento.REAGENDADO

        self.repository.salvar_agendamento(agendamento)

        logger.info(
            "Agendamento %s reagendado para %s",
            agendamento.id,
            novo_slot.inicio.isoformat(),
        )

        return agendamento

    def cancelar(self, agendamento_id: str) -> Agendamento:

        agendamento = self.repository.obter_agendamento(agendamento_id)

        if agendamento is None:
            raise AgendamentoNaoEncontradoError(
                f"Agendamento {agendamento_id!r} não encontrado."
            )

        slot = self.repository.obter_slot(agendamento.slot_id)

        if slot is not None:
            slot.ocupado = False
            self.repository.salvar_slot(slot)

        agendamento.status = StatusAgendamento.CANCELADO
        self.repository.salvar_agendamento(agendamento)

        logger.info("Agendamento %s cancelado", agendamento.id)

        return agendamento
