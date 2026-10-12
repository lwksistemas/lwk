"""PDFs da clínica. A gravação no servidor de mídia fica em core.media_pdf."""
import logging
import re

from core.media_pdf import (
    PASTA_PDF_LOJA,
    arquivar_pdf_gerado,
    salvar_pdf_loja,
)
from core.media_pdf import (
    salvar_pdf_pessoa as salvar_pdf_paciente,
)

logger = logging.getLogger(__name__)

__all__ = [
    "PASTA_PDF_LOJA",
    "arquivar_pdf_gerado",
    "salvar_pdf_loja",
    "salvar_pdf_paciente",
]


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
