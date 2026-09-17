"""Remove fotos e PDFs da consulta no servidor de mídia ao excluir não finalizada."""
from __future__ import annotations

import logging
import re

from core.media_storage import (
    media_delete_by_url,
    media_delete_tenant,
    media_list_files,
    normalize_media_tenant,
    parse_media_url,
    pasta_media_paciente,
)

from .memed_prescricao_service import nome_arquivo_pdf_prescricao
from .prontuario_pdf.generators import SECOES_CONSULTA_PDF

logger = logging.getLogger(__name__)


def _tenant_loja(loja_id) -> str:
    from superadmin.models import Loja

    loja = Loja.objects.using("default").filter(id=loja_id).first()
    if not loja:
        return ""
    return normalize_media_tenant(re.sub(r"\D", "", loja.cpf_cnpj or ""))


def _paciente_consulta(consulta):
    patient = getattr(consulta, "patient", None)
    if patient is not None:
        return patient
    pid = getattr(consulta, "patient_id", None)
    if not pid:
        return None
    from .models import Patient

    return Patient.objects.filter(pk=pid).first()


def nomes_pdf_da_consulta(consulta) -> set[str]:
    """Nomes de arquivo no {paciente}/pdf/ que pertencem a esta consulta."""
    from .models import DocumentoClinico, OrcamentoConsulta, PrescricaoMemed

    pk = consulta.pk
    nomes: set[str] = {f"consulta_{pk}_{secao}.pdf" for secao in SECOES_CONSULTA_PDF}

    for doc in DocumentoClinico.objects.filter(consulta_id=pk).only("id", "tipo"):
        tipo = (doc.tipo or "documento").strip() or "documento"
        nomes.add(f"{tipo}_{doc.id}.pdf")

    for presc in PrescricaoMemed.objects.filter(consulta_id=pk).only(
        "id", "prescricao_id", "pdf_url",
    ):
        nomes.add(nome_arquivo_pdf_prescricao(presc.prescricao_id, presc.pk))
        parsed = parse_media_url((presc.pdf_url or "").strip())
        if parsed:
            nomes.add(parsed[2])

    for orc in OrcamentoConsulta.objects.filter(consulta_id=pk).only("id"):
        nomes.add(f"orcamento_{orc.id}.pdf")
        nomes.add(f"orcamento_{orc.id}_")  # prefixo: orcamento_{id}_{data}.pdf

    return nomes


def _arquivo_pdf_da_consulta(filename: str, consulta_id: int, conhecidos: set[str]) -> bool:
    if not filename or not filename.lower().endswith(".pdf"):
        return False
    if filename in conhecidos:
        return True
    if filename.startswith(f"consulta_{consulta_id}_"):
        return True
    if filename.startswith("termo_") and filename.endswith(f"_{consulta_id}.pdf"):
        return True
    for marca in conhecidos:
        if marca.endswith("_") and filename.startswith(marca):
            return True
    return False


def limpar_pdfs_media_da_consulta(consulta) -> int:
    """Apaga PDFs da consulta no Magalu. Chamar ANTES de consulta.delete()."""
    from .models import PrescricaoMemed

    patient = _paciente_consulta(consulta)
    tenant = _tenant_loja(consulta.loja_id)
    if not patient or not tenant:
        removidos = 0
        for presc in PrescricaoMemed.objects.filter(consulta_id=consulta.pk).only("pdf_url"):
            url = (presc.pdf_url or "").strip()
            if url:
                try:
                    if media_delete_by_url(url):
                        removidos += 1
                except Exception:
                    logger.exception(
                        "Falha ao remover PDF da prescrição consulta %s", consulta.pk,
                    )
        return removidos

    folder = f"{pasta_media_paciente(patient)}/pdf"
    conhecidos = nomes_pdf_da_consulta(consulta)
    alvos = {n for n in conhecidos if n.lower().endswith(".pdf")}

    listagem = {}
    try:
        listagem = media_list_files(tenant, folder) or {}
    except Exception:
        logger.exception("Falha ao listar PDFs da consulta %s em %s/%s", consulta.pk, tenant, folder)
    for item in listagem.get("files") or []:
        nome = (item.get("filename") or "").strip()
        if _arquivo_pdf_da_consulta(nome, consulta.pk, conhecidos):
            alvos.add(nome)

    removidos = 0
    for nome in alvos:
        try:
            if media_delete_tenant(tenant, nome, folder=folder):
                removidos += 1
        except Exception:
            logger.exception(
                "Falha ao remover PDF %s da consulta %s", nome, consulta.pk,
            )
    return removidos


def limpar_midia_da_consulta(consulta) -> int:
    """Fotos + PDFs da consulta. Prescrições Memed desta consulta também são apagadas.

    PrescricaoMemed.consulta é SET_NULL: sem este passo o PDF ficaria órfão no Magalu
    e a receita continuaria no histórico do paciente após excluir consulta não finalizada.
    """
    from .foto_paciente_service import limpar_fotos_media_da_consulta
    from .models import PrescricaoMemed

    n = limpar_fotos_media_da_consulta(consulta)
    n += limpar_pdfs_media_da_consulta(consulta)
    PrescricaoMemed.objects.filter(consulta_id=consulta.pk).delete()
    return n
