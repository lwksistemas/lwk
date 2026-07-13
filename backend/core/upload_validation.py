"""Validação básica de uploads (tamanho, extensão, magic bytes).
"""
from __future__ import annotations

MAX_XML_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_PDF_BYTES = 5 * 1024 * 1024


def validate_uploaded_file(
    uploaded_file,
    *,
    allowed_extensions: tuple[str, ...],
    max_bytes: int,
    magic_prefixes: tuple[bytes, ...] | None = None,
) -> tuple[bool, str]:
    if not uploaded_file:
        return False, "Arquivo não enviado."

    name = (getattr(uploaded_file, "name", "") or "").lower()
    if allowed_extensions and not any(name.endswith(ext) for ext in allowed_extensions):
        return False, f'Extensão inválida. Permitido: {", ".join(allowed_extensions)}'

    size = getattr(uploaded_file, "size", None)
    if size is None:
        try:
            pos = uploaded_file.tell()
            uploaded_file.seek(0, 2)
            size = uploaded_file.tell()
            uploaded_file.seek(pos)
        except Exception:
            size = None

    if size is not None and size > max_bytes:
        mb = max_bytes // (1024 * 1024)
        return False, f"Arquivo muito grande (máx. {mb} MB)."

    if magic_prefixes:
        try:
            head = uploaded_file.read(32)
            uploaded_file.seek(0)
        except Exception:
            return False, "Não foi possível ler o arquivo."
        if not any(head.startswith(prefix) for prefix in magic_prefixes):
            return False, "Conteúdo do arquivo não corresponde ao tipo esperado."

    return True, ""


def validate_xml_upload(uploaded_file) -> tuple[bool, str]:
    return validate_uploaded_file(
        uploaded_file,
        allowed_extensions=(".xml",),
        max_bytes=MAX_XML_BYTES,
        magic_prefixes=(b"<?xml", b"<", b"\xef\xbb\xbf<?"),  # UTF-8 BOM + XML
    )


def validate_pdf_upload(uploaded_file) -> tuple[bool, str]:
    return validate_uploaded_file(
        uploaded_file,
        allowed_extensions=(".pdf",),
        max_bytes=MAX_PDF_BYTES,
        magic_prefixes=(b"%PDF",),
    )
