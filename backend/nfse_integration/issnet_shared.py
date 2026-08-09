"""Constantes e helpers compartilhados entre ISSNet loja e superadmin."""
from datetime import date
from typing import Any

CODIGOS_CANCELAMENTO = {
    "1": "Erro na emissão",
    "2": "Serviço não prestado",
    "3": "Erro de assinatura",
    "4": "Duplicidade da nota",
}

# Ribeirão Preto: ABRASF legado deixa de ser aceito a partir desta data.
ISSNET_NACIONAL_OBRIGATORIO_DESDE = date(2026, 7, 31)


def normalizar_codigo_cancelamento(codigo: str | int | None) -> str:
    codigo_str = str(codigo or "1")
    return codigo_str if codigo_str in CODIGOS_CANCELAMENTO else "1"


def usar_issnet_padrao_nacional(config: Any | None) -> bool:
    """True se a loja deve usar ISSNet Nacional (DPS/RTC).

    Respeita `issnet_usar_padrao_nacional` e força Nacional a partir de
    31/07/2026 (descontinuação ABRASF em Ribeirão Preto).
    """
    if config is None:
        return False
    if bool(getattr(config, "issnet_usar_padrao_nacional", False)):
        return True
    return date.today() >= ISSNET_NACIONAL_OBRIGATORIO_DESDE
