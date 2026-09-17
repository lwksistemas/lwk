"""Views de Agenda, Bloqueios de Horário e Agendamentos — Clínica da Beleza."""
from .agendamento import (
    AgendaCreateView,
    AgendaDeleteView,
    AgendaReenviarMensagemView,
    AgendaUpdateView,
)
from .bloqueios import BloqueioHorarioDetailView, BloqueioHorarioListView
from .calendario import AgendaView
from .helpers import _agenda_events_queryset

__all__ = [
    "AgendaCreateView",
    "AgendaDeleteView",
    "AgendaReenviarMensagemView",
    "AgendaUpdateView",
    "AgendaView",
    "BloqueioHorarioDetailView",
    "BloqueioHorarioListView",
    "_agenda_events_queryset",
]
