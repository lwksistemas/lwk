"""Webhook Asaas por loja — conta Asaas da clínica da beleza (NFS-e / cobranças).

Cada loja configura no painel Asaas (Integrações → Webhooks) a URL:
  POST {API}/api/clinica-beleza/webhooks/asaas/<slug_loja>/
"""
import logging

from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from tenants.middleware import (
    _configure_tenant_db_for_loja,
    resolve_loja_from_slug_or_cnpj,
)

logger = logging.getLogger(__name__)


@csrf_exempt
@api_view(["GET", "POST", "HEAD"])
@permission_classes([AllowAny])
def clinica_beleza_asaas_webhook(request, loja_slug: str):
    """Recebe notificações do Asaas da conta configurada na clínica.

    GET/HEAD: confirma que a URL está correta.
    POST: eventos PAYMENT_*, INVOICE_* — valida token e processa.
    """
    loja = resolve_loja_from_slug_or_cnpj(loja_slug.strip())
    if not loja:
        return Response(
            {"error": "Loja não encontrada", "slug": loja_slug},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method in ("GET", "HEAD"):
        return Response({
            "ok": True,
            "message": "Webhook Asaas (Clínica Beleza) ativo.",
            "loja_slug": loja.slug,
            "loja_id": loja.id,
        })

    if not _configure_tenant_db_for_loja(loja, request):
        logger.warning(
            "clinica_beleza_asaas_webhook: falha tenant loja_id=%s", loja.id,
        )

    from core.webhook_security import (
        verify_asaas_access_token,
        webhook_auth_failed_response,
    )

    from .models import ClinicaBelezaNFSeConfig

    # Buscar token do webhook da config da clínica
    config = ClinicaBelezaNFSeConfig.objects.filter(loja_id=loja.id).first()
    loja_token = ""
    if config:
        raw = getattr(config, "asaas_webhook_token", "") or ""
        if raw:
            from core.encryption import decrypt_value
            try:
                loja_token = decrypt_value(raw)
            except Exception:
                loja_token = raw

    if not verify_asaas_access_token(request, expected_token=loja_token or None):
        return webhook_auth_failed_response()

    payload = request.data if isinstance(request.data, dict) else {}
    event = payload.get("event") or payload.get("type")
    payment = payload.get("payment") if isinstance(payload.get("payment"), dict) else {}

    logger.info(
        "Asaas webhook clinica slug=%s id=%s event=%s payment_id=%s",
        loja.slug, loja.id, event, payment.get("id"),
    )

    # Reutilizar processamento do CRM (mesma lógica de NFS-e por loja)
    from asaas_integration.queue_dispatch import (
        enqueue_asaas_loja_webhook,
        should_enqueue_asaas_webhook,
    )
    from crm_vendas.asaas_loja_webhook_process import (
        process_asaas_loja_webhook_sync,
    )

    if should_enqueue_asaas_webhook():
        enqueue_asaas_loja_webhook(loja.id, payload)
        return Response({
            "status": "received", "queued": True,
            "loja_slug": loja.slug, "event": event,
        })

    process_asaas_loja_webhook_sync(loja.id, payload)
    return Response({
        "status": "received",
        "loja_slug": loja.slug, "event": event,
    })
