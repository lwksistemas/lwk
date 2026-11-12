"""Validade do link público do termo de consentimento."""

CONSULTA_STATUS_LINK_ENCERRADO = frozenset({"COMPLETED", "CANCELLED"})


def termo_link_expirado_por_consulta(status: str | None) -> bool:
    """O link vale enquanto a consulta não estiver concluída ou cancelada."""
    return not status or status in CONSULTA_STATUS_LINK_ENCERRADO


def mensagem_envio_termo_encerrado(status: str | None) -> str | None:
    """Consulta concluída ou cancelada não recebe novo envio para assinatura."""
    if status == "CANCELLED":
        return "Consulta cancelada. O termo não pode mais ser enviado para assinatura."
    if status == "COMPLETED":
        return "Consulta finalizada. O termo não pode mais ser enviado para assinatura."
    return None
