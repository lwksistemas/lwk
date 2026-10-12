"""Grava PDF no servidor de mídia, na pasta da loja. Não pertence a um app."""
import logging
import re
from typing import Any

from core.media_storage import media_upload_tenant, normalize_media_tenant, pasta_media_paciente

logger = logging.getLogger(__name__)

PASTA_PDF_LOJA = "admin/pdf"


def _resolver_tenant_loja(loja_id: int) -> str | None:
    from superadmin.models import Loja

    loja = Loja.objects.using("default").filter(id=loja_id).first()
    if not loja:
        return None
    cpf_cnpj = re.sub(r"\D", "", loja.cpf_cnpj or "")
    return normalize_media_tenant(cpf_cnpj)


def salvar_pdf_loja(loja_id: int, pdf_bytes: bytes, filename: str) -> str | None:
    """Salva PDF da loja em admin/pdf/."""
    tenant = _resolver_tenant_loja(loja_id)
    if not tenant or not pdf_bytes:
        return None
    try:
        url = media_upload_tenant(tenant, pdf_bytes, filename=filename, folder=PASTA_PDF_LOJA)
        if url:
            logger.info("PDF da loja salvo: %s/%s/%s", tenant, PASTA_PDF_LOJA, filename)
        return url
    except Exception as exc:
        logger.warning("Erro ao salvar PDF da loja %s: %s", filename, exc)
        return None


def salvar_pdf_pessoa(loja_id: int, pessoa: Any, pdf_bytes: bytes, filename: str) -> str | None:
    """Salva PDF em /{cnpj}/{pessoa}/pdf/."""
    tenant = _resolver_tenant_loja(loja_id)
    if not tenant:
        logger.warning("salvar_pdf_pessoa: loja %s sem tenant válido", loja_id)
        return None
    if not pessoa or not pdf_bytes:
        return None

    slug = pasta_media_paciente(pessoa)
    folder = f"{slug}/pdf"
    url = media_upload_tenant(tenant, pdf_bytes, filename=filename, folder=folder)
    if url:
        logger.info("PDF salvo no servidor de mídia: %s/%s/%s", tenant, folder, filename)
    else:
        logger.warning("Falha ao salvar PDF no servidor de mídia: %s/%s/%s", tenant, folder, filename)
    return url


def arquivar_pdf_gerado(
    loja_id: int | None,
    pessoa: Any,
    pdf_bytes: bytes | None,
    filename: str,
) -> str | None:
    """Arquiva PDF gerado sem interromper o fluxo principal."""
    if not loja_id or not pessoa or not pdf_bytes:
        return None
    try:
        return salvar_pdf_pessoa(int(loja_id), pessoa, pdf_bytes, filename)
    except Exception as exc:
        logger.warning("Erro ao arquivar PDF %s: %s", filename, exc)
        return None
