"""Pastas DICOM no media server + sincronização Orthanc → paciente (isolamento por loja)."""
from __future__ import annotations

import logging

from django.utils import timezone

from core.media_storage import folder_media_paciente_cpf, media_upload_empresa

from .models import PedidoExame
from .orthanc_service import (
    download_study_archive,
    find_orthanc_study_for_pedido,
    validate_study_belongs_to_pedido,
)

logger = logging.getLogger(__name__)


def folder_dicom_paciente(paciente) -> str:
    """Pasta relativa: dicom/{cpf}/ dentro de {cnpj}_{nome-empresa}/."""
    return folder_media_paciente_cpf("dicom", paciente)


def sincronizar_imagens_pedido(pedido: PedidoExame) -> PedidoExame:
    """Localiza estudo no Orthanc, valida tenant/paciente e arquiva ZIP na pasta do paciente."""
    from superadmin.models import Loja

    if not pedido.study_instance_uid:
        raise ValueError("Pedido sem StudyInstanceUID")

    meta = find_orthanc_study_for_pedido(pedido)
    if not meta:
        raise LookupError(
            "Estudo ainda não chegou ao PACS. Confira C-STORE do ultrassom e Accession/UID do pedido."
        )

    if not validate_study_belongs_to_pedido(pedido, meta):
        pedido.status = PedidoExame.Status.ORFAO
        pedido.save(update_fields=["status", "updated_at"])
        raise PermissionError(
            "Estudo no PACS não confere com paciente/loja deste pedido (possível mistura — bloqueado)."
        )

    orthanc_id = meta.get("orthanc_id") or ""
    archive = download_study_archive(orthanc_id)
    if not archive:
        raise RuntimeError("Falha ao exportar estudo do Orthanc")

    loja = Loja.objects.using("default").filter(id=pedido.loja_id).first()
    if not loja:
        raise RuntimeError("Loja não encontrada")

    acc = (pedido.accession_number or f"pedido{pedido.id}").replace("/", "_")
    filename = f"{acc}.zip"
    folder = folder_dicom_paciente(pedido.paciente)
    media_url = media_upload_empresa(loja, archive, filename=filename, folder=folder) or ""

    pedido.orthanc_study_id = orthanc_id
    pedido.dicom_media_url = media_url
    pedido.dicom_instance_count = int(meta.get("instance_count") or 0)
    pedido.dicom_synced_at = timezone.now()
    if pedido.status in (
        PedidoExame.Status.AGENDADO,
        PedidoExame.Status.NA_WORKLIST,
        PedidoExame.Status.EM_AQUISICAO,
    ):
        pedido.status = PedidoExame.Status.IMAGENS_RECEBIDAS
    pedido.save(
        update_fields=[
            "orthanc_study_id",
            "dicom_media_url",
            "dicom_instance_count",
            "dicom_synced_at",
            "status",
            "updated_at",
        ]
    )
    logger.info(
        "DICOM arquivado loja=%s pedido=%s pasta=%s url=%s",
        pedido.loja_id,
        pedido.id,
        folder,
        media_url[:80] if media_url else "",
    )
    return pedido
