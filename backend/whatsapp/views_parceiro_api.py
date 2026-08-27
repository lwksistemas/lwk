"""API pública autenticada por chave de parceiro (não expõe a Evolution)."""
from __future__ import annotations

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from superadmin.services.whatsapp_painel_service import buscar_chave


def _bearer_token(request) -> str:
    header = request.META.get("HTTP_AUTHORIZATION") or ""
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return (request.headers.get("X-Api-Key") or "").strip()


class WhatsappParceiroMeView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        key = buscar_chave(_bearer_token(request))
        if not key:
            return Response({"error": "Chave inválida ou revogada."}, status=status.HTTP_401_UNAUTHORIZED)
        key.last_used_at = timezone.now()
        key.save(update_fields=["last_used_at"])
        c = key.customer
        return Response(
            {
                "customer_id": c.id,
                "nome": c.nome,
                "documento": c.documento,
                "tipo": c.tipo,
                "quota_numeros": c.quota_numeros,
                "ativo": c.is_active,
                "gateway": "lwk",
            }
        )
