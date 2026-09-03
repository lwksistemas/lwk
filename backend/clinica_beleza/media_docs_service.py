"""Service para salvar PDFs gerados na pasta do paciente/cliente.

Estrutura: /storage/{cnpj}/{paciente_slug}/pdf/{arquivo}.pdf
"""
import logging
import re
from typing import Any

from core.media_storage import media_upload_tenant, normalize_media_tenant, pasta_media_paciente

logger = logging.getLogger(__name__)


def _resolver_tenant_loja(loja_id: int) -> str | None:
    """Resolve o tenant (CNPJ dígitos) da loja."""
    from superadmin.models import Loja

    loja = Loja.objects.using("default").filter(id=loja_id).first()
    if not loja:
        return None
    cpf_cnpj = re.sub(r"\D", "", loja.cpf_cnpj or "")
    return normalize_media_tenant(cpf_cnpj)


def salvar_pdf_paciente(
    loja_id: int,
    patient: Any,
    pdf_bytes: bytes,
    filename: str,
) -> str | None:
    """Salva PDF na pasta pdf/ do paciente ou cliente no servidor de mídia."""
    tenant = _resolver_tenant_loja(loja_id)
    if not tenant:
        logger.warning("salvar_pdf_paciente: loja %s sem tenant válido", loja_id)
        return None
    if not patient or not pdf_bytes:
        return None

    slug = pasta_media_paciente(patient)
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
        return salvar_pdf_paciente(int(loja_id), pessoa, pdf_bytes, filename)
    except Exception as exc:
        logger.warning("Erro ao arquivar PDF %s: %s", filename, exc)
        return None


def _salvar_termo_no_servidor_midia(adapter, termo_proc, loja_id: int) -> str | None:
    """Salva o PDF do termo de consentimento assinado na pasta pdf/ do paciente."""
    try:
        pdf_buffer = adapter.gerar_pdf(termo_proc, incluir_assinaturas=True)
        pdf_buffer.seek(0)
        pdf_bytes = pdf_buffer.read()

        patient = getattr(termo_proc, "patient", None)
        if not patient:
            consulta = getattr(termo_proc, "consulta", None)
            if consulta:
                patient = getattr(consulta, "patient", None)

        if not patient:
            logger.warning("_salvar_termo_no_servidor_midia: paciente não encontrado")
            return None

        proc_nome = ""
        procedure = getattr(termo_proc, "procedure", None)
        if procedure:
            proc_nome = re.sub(r"[^a-z0-9]+", "-", procedure.nome.lower()).strip("-")[:30]

        from django.utils import timezone
        data = timezone.now().strftime("%Y%m%d")
        filename = f"termo_{proc_nome}_{data}.pdf" if proc_nome else f"termo_consentimento_{data}.pdf"

        return salvar_pdf_paciente(loja_id, patient, pdf_bytes, filename)
    except Exception as e:
        logger.warning("Erro ao salvar termo no servidor de mídia: %s", e)
        return None


def salvar_orcamento_no_servidor_midia(orcamento, pdf_bytes: bytes) -> str | None:
    """Salva o PDF do orçamento no servidor de mídia ({paciente}/pdf/)."""
    try:
        patient = orcamento.patient
        if not patient:
            return None

        from django.utils import timezone
        data = timezone.now().strftime("%Y%m%d")
        filename = f"orcamento_{orcamento.id}_{data}.pdf"

        return salvar_pdf_paciente(orcamento.loja_id, patient, pdf_bytes, filename)
    except Exception as e:
        logger.warning("Erro ao salvar orçamento no servidor de mídia: %s", e)
        return None
