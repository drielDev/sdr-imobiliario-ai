from datetime import datetime
from typing import Protocol


class Relogio(Protocol):
    """Fonte de tempo injetável. Permite testar follow-up e agendamento
    sem depender do relógio real do sistema nem esperar tempo passar."""

    def agora(self) -> datetime:
        ...


class RelogioSistema:

    def agora(self) -> datetime:

        return datetime.now()
