"""Grava o .pfx cifrado e só aceita upload que o PKCS#12 consegue abrir."""
from __future__ import annotations

from core.encryption import decrypt_bytes, decrypt_value, encrypt_bytes


class CertificadoInvalido(Exception):
    """O arquivo não é um PKCS#12 que abre com a senha informada."""


def ler_pfx(data: bytes | None) -> bytes:
    """Devolve o .pfx em claro. Blob antigo, sem prefixo, passa direto."""
    return decrypt_bytes(data or b"")


def validar_pfx(data: bytes, senha: str) -> None:
    """Abre o PKCS#12. Falha com mensagem única, sem detalhe da biblioteca."""
    from cryptography.hazmat.primitives.serialization import pkcs12

    if not data:
        raise CertificadoInvalido("Envie o arquivo .pfx.")
    try:
        chave, certificado, _extra = pkcs12.load_key_and_certificates(
            data, (senha or "").encode("utf-8"),
        )
    except Exception as exc:
        raise CertificadoInvalido(
            "O certificado ou a senha não abrem o arquivo .pfx.",
        ) from exc
    if chave is None or certificado is None:
        raise CertificadoInvalido(
            "O arquivo .pfx não contém certificado e chave privada.",
        )


def preparar_pfx_para_gravar(data: bytes, senha: str) -> bytes:
    """Valida o PKCS#12 e devolve o blob cifrado para o BinaryField."""
    if not (senha or "").strip():
        raise CertificadoInvalido("Informe a senha do certificado para validar o .pfx.")
    validar_pfx(data, senha)
    return encrypt_bytes(data)


def senha_do_upload(data, *guardadas: str) -> str:
    """Senha digitada agora, ou a que já está cifrada na configuração."""
    for campo in ("nacional_senha_certificado", "issnet_senha_certificado"):
        if not hasattr(data, "get") or campo not in data:
            continue
        bruto = data.get(campo)
        if isinstance(bruto, (list, tuple)):
            bruto = bruto[0] if bruto else ""
        texto = str(bruto or "").strip()
        if texto and "..." not in texto:
            return texto
    for guardada in guardadas:
        aberta = decrypt_value(guardada or "")
        if aberta:
            return aberta
    return ""
