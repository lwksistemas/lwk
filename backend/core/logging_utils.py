"""Helpers para logs seguros."""


def mask_email(email: str | None) -> str:
    """Mascara e-mails em logs preservando rastreabilidade sem expor o endereço completo."""
    if not email or "@" not in email:
        return ""

    local, domain = email.split("@", 1)
    if not local or not domain:
        return "***"

    visible_local = local[:2] if len(local) > 2 else local[:1]
    domain_parts = domain.split(".", 1)
    visible_domain = domain_parts[0][:2] if domain_parts and domain_parts[0] else ""
    suffix = f".{domain_parts[1]}" if len(domain_parts) > 1 else ""
    return f"{visible_local}***@{visible_domain}***{suffix}"
