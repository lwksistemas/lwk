"""Serviços de domínio do RIS."""
from __future__ import annotations

import logging

from django.utils import timezone

from .models import Laudo, PedidoExame
from .orthanc_service import (
    gerar_accession_number,
    gerar_study_instance_uid,
    remove_pedido_mwl,
    sync_pedido_mwl,
)

logger = logging.getLogger(__name__)


def preparar_pedido_uids(pedido: PedidoExame) -> PedidoExame:
    """Garante AccessionNumber e StudyInstanceUID gerados no RIS (após save com id)."""
    if not pedido.id:
        pedido.save()
    update = []
    acc = gerar_accession_number(pedido.loja_id, pedido.id)
    uid = gerar_study_instance_uid(pedido.loja_id, pedido.id)
    if pedido.accession_number != acc:
        pedido.accession_number = acc
        update.append("accession_number")
    if not pedido.study_instance_uid:
        pedido.study_instance_uid = uid
        update.append("study_instance_uid")
    if update:
        update.append("updated_at")
        pedido.save(update_fields=update)
    return pedido


def publicar_pedido_na_worklist(pedido: PedidoExame) -> PedidoExame:
    preparar_pedido_uids(pedido)
    ok = sync_pedido_mwl(pedido)
    if not ok:
        logger.warning("Pedido %s não sincronizou MWL (Orthanc offline ou dir inválido)", pedido.id)
    return pedido


def cancelar_pedido(pedido: PedidoExame) -> PedidoExame:
    remove_pedido_mwl(pedido)
    pedido.status = PedidoExame.Status.CANCELADO
    pedido.save(update_fields=["status", "updated_at"])
    return pedido


def obter_ou_criar_laudo(pedido: PedidoExame) -> Laudo:
    laudo, created = Laudo.objects.get_or_create(
        pedido=pedido,
        defaults={
            "loja_id": pedido.loja_id,
            "texto": (pedido.procedimento.template_laudo or "").strip(),
        },
    )
    if created and pedido.status not in (
        PedidoExame.Status.LAUDADO,
        PedidoExame.Status.ENTREGUE,
        PedidoExame.Status.CANCELADO,
    ):
        pedido.status = PedidoExame.Status.EM_LAUDO
        pedido.save(update_fields=["status", "updated_at"])
    return laudo


def finalizar_laudo(laudo: Laudo, *, assinar: bool = False) -> Laudo:
    from .laudo_pdf import gerar_pdf_laudo

    pdf_bytes = gerar_pdf_laudo(laudo)
    pdf_url = ""
    try:
        from core.media_storage import media_upload
        from superadmin.models import Loja

        loja = Loja.objects.using("default").filter(id=laudo.loja_id).first()
        if loja and pdf_bytes:
            pdf_url = media_upload(loja, pdf_bytes, filename="laudo.pdf", folder="docs") or ""
    except Exception as exc:
        logger.warning("Falha ao arquivar PDF do laudo: %s", exc)

    laudo.pdf_url = pdf_url or laudo.pdf_url
    laudo.status = Laudo.Status.ASSINADO if assinar else Laudo.Status.FINALIZADO
    if assinar:
        laudo.assinado_em = timezone.now()
    laudo.save(
        update_fields=["pdf_url", "status", "assinado_em", "updated_at", "texto", "conclusao", "bi_rads", "medico_laudador", "crm_laudador"]
    )

    pedido = laudo.pedido
    pedido.status = PedidoExame.Status.LAUDADO
    pedido.save(update_fields=["status", "updated_at"])
    return laudo


def gerar_pdf_laudo_bytes(laudo: Laudo) -> bytes:
    from .laudo_pdf import gerar_pdf_laudo

    return gerar_pdf_laudo(laudo)
