"""Quem recebe o backup automático da loja."""


def filtrar_emails_backup(email_administrador_sistema: str, pessoas: list[dict]) -> list[str]:
    """E-mail do administrador do sistema e de quem tem perfil Administrador.

    Vendedor comum não entra.
    pessoas: {"email": str, "recebe_backup": bool}
    """
    saida: list[str] = []
    vistos: set[str] = set()
    dono = (email_administrador_sistema or "").strip()
    if dono:
        saida.append(dono)
        vistos.add(dono.lower())
    for pessoa in pessoas:
        if not pessoa.get("recebe_backup"):
            continue
        email = (pessoa.get("email") or "").strip()
        chave = email.lower()
        if not chave or chave in vistos:
            continue
        vistos.add(chave)
        saida.append(email)
    return saida
