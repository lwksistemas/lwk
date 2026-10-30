"""Configuração e webhook da Cora (conta da LWK)."""

import logging

from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger(__name__)


def _exigir_superadmin(request):
    if not request.user.is_superuser:
        return Response({"detail": "Sem permissão."}, status=status.HTTP_403_FORBIDDEN)
    return None


def _serializar(config) -> dict:
    return {
        "enabled": config.enabled,
        "use_for_boletos": config.use_for_boletos,
        "client_id": config.client_id,
        "credential_ready": config.credencial_pronta,
    }


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def cora_config(request):
    from ..models import CoraConfig, MercadoPagoConfig

    negado = _exigir_superadmin(request)
    if negado:
        return negado
    config = CoraConfig.get_config()
    if request.method == "GET":
        return Response(_serializar(config))
    if "enabled" in request.data:
        config.enabled = bool(request.data.get("enabled"))
    if "client_id" in request.data:
        config.client_id = str(request.data.get("client_id") or "").strip()[:80]
    if "use_for_boletos" in request.data:
        config.use_for_boletos = bool(request.data.get("use_for_boletos"))
        if config.use_for_boletos:
            mp = MercadoPagoConfig.get_config()
            if mp.use_for_boletos:
                mp.use_for_boletos = False
                mp.save(update_fields=["use_for_boletos"])
    config.save()
    return Response(_serializar(config))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cora_test(request):
    from ..cora_service import cliente_da_config

    negado = _exigir_superadmin(request)
    if negado:
        return negado
    try:
        client, _config = cliente_da_config()
        resultado = client.testar()
    except Exception:
        logger.exception("Teste Cora falhou")
        return Response({"success": False, "error": "Não foi possível falar com a Cora."}, status=status.HTTP_400_BAD_REQUEST)
    if not resultado.get("success"):
        return Response(resultado, status=status.HTTP_400_BAD_REQUEST)
    webhook = request.build_absolute_uri("/api/superadmin/cora-webhook/")
    segredo = _segredo_webhook_cora()
    if segredo:
        webhook = f"{webhook}?token={segredo}"
    try:
        client.registrar_webhook(webhook)
        resultado["webhook"] = "registrado"
    except Exception:
        logger.warning("Webhook da Cora não foi registrado automaticamente")
        resultado["webhook"] = webhook
    return Response(resultado)


def _segredo_webhook_cora() -> str:
    from django.conf import settings

    return (getattr(settings, "CORA_WEBHOOK_SECRET", None) or "").strip()


def _cora_webhook_autorizado(request) -> bool:
    """A Cora não assina o POST. Com CORA_WEBHOOK_SECRET, a URL registrada leva ?token=."""
    from core.webhook_security import secrets_match

    segredo = _segredo_webhook_cora()
    if not segredo:
        return True
    recebido = (
        request.headers.get("X-Cora-Webhook-Token")
        or request.query_params.get("token")
        or ""
    ).strip()
    return secrets_match(recebido, segredo)


def _cora_dentro_do_limite(request) -> bool:
    from django.core.cache import cache

    from core.rate_limit import _get_client_ip

    ip = _get_client_ip(request)
    chave = f"rl:cora-webhook:{ip}"
    total = cache.get(chave, 0)
    if total >= 60:
        return False
    if total == 0:
        cache.set(chave, 1, 60)
    else:
        ttl = cache.ttl(chave) if hasattr(cache, "ttl") else 60
        cache.set(chave, int(total) + 1, ttl or 60)
    return True


@csrf_exempt
@api_view(["POST"])
@permission_classes([])
def cora_webhook(request):
    """Aviso da Cora. O pagamento só renova a loja depois de a API confirmar status PAID."""
    if not _cora_webhook_autorizado(request):
        return Response({"status": "unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
    if not _cora_dentro_do_limite(request):
        return Response({"status": "limited"}, status=status.HTTP_429_TOO_MANY_REQUESTS)
    tipo = (request.headers.get("webhook-event-type") or "").strip()
    invoice_id = (request.headers.get("webhook-resource-id") or "").strip()
    if tipo != "invoice.paid" or not invoice_id:
        return Response({"status": "ignored"}, status=status.HTTP_200_OK)
    from ..cora_service import confirmar_fatura_paga

    try:
        confirmar_fatura_paga(invoice_id)
    except Exception:
        logger.exception("Erro ao processar webhook Cora")
    return Response({"status": "ok"}, status=status.HTTP_200_OK)
