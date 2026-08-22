"""Configuração singleton do consultório."""
from datetime import time

from tenants.middleware import get_current_loja_id

from .models import ConfiguracaoConsultorio


def get_or_create_config() -> ConfiguracaoConsultorio:
    loja_id = get_current_loja_id()
    config = ConfiguracaoConsultorio.objects.first()
    if config:
        return config
    defaults = {"hora_inicio": time(8, 0), "hora_fim": time(18, 0), "duracao_minutos": 15}
    if loja_id:
        defaults["loja_id"] = loja_id
    return ConfiguracaoConsultorio.objects.create(**defaults)


def agenda_janela(config: ConfiguracaoConsultorio | None = None) -> tuple[time, time, int]:
    config = config or ConfiguracaoConsultorio.objects.first()
    if not config:
        return time(8, 0), time(18, 0), 15
    return config.hora_inicio, config.hora_fim, config.duracao_minutos or 15
