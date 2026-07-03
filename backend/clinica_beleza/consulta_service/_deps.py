"""Dependências compartilhadas — re-exportadas em consulta_service para compatibilidade com testes."""

import logging

from ..models import Appointment, Consulta, Payment

logger = logging.getLogger(__name__)

__all__ = ["Appointment", "Consulta", "Payment", "logger"]
