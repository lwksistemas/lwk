"""Validade do link público do termo de consentimento."""

CONSULTA_STATUS_LINK_ENCERRADO = frozenset({"COMPLETED", "CANCELLED"})


def termo_link_expirado_por_consulta(status: str | None) -> bool:
    """O link vale enquanto a consulta não estiver concluída ou cancelada."""
    return not status or status in CONSULTA_STATUS_LINK_ENCERRADO
