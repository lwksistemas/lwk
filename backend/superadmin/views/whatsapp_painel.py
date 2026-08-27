"""API SuperAdmin do painel WhatsApp (clientes, números e chaves de parceiro)."""
from __future__ import annotations

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from superadmin.models import WhatsappApiKey, WhatsappCustomer
from superadmin.services.whatsapp_painel_service import (
    QUOTA_PARCEIRO_PADRAO,
    criar_parceiro,
    emitir_chave,
    montar_painel,
)
from superadmin.views.permissions import IsSuperAdmin


def _quota_do_pedido(data) -> int:
    raw = data.get("quota_numeros")
    if raw in (None, ""):
        return QUOTA_PARCEIRO_PADRAO
    return raw


class WhatsappPainelView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        return Response(montar_painel())


class WhatsappParceiroCreateView(APIView):
    permission_classes = [IsSuperAdmin]

    def post(self, request):
        try:
            customer = criar_parceiro(
                nome=request.data.get("nome") or "",
                documento=request.data.get("documento") or request.data.get("cpf_cnpj") or "",
                quota_numeros=_quota_do_pedido(request.data),
                webhook_url=request.data.get("webhook_url") or "",
            )
            key, raw = emitir_chave(customer, nome=request.data.get("nome_chave") or "php")
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {
                "id": customer.id,
                "nome": customer.nome,
                "documento": customer.documento,
                "quota_numeros": customer.quota_numeros,
                "tipo": customer.tipo,
                "chave": raw,
                "aviso": "Copie agora. A chave completa não será exibida de novo.",
            },
            status=status.HTTP_201_CREATED,
        )


class WhatsappParceiroChaveView(APIView):
    permission_classes = [IsSuperAdmin]

    def post(self, request, customer_id: int):
        customer = WhatsappCustomer.objects.filter(id=customer_id).first()
        if not customer:
            return Response({"error": "Parceiro não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        try:
            key, raw = emitir_chave(customer, nome=request.data.get("nome") or "padrão")
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {
                "id": key.id,
                "prefixo": key.prefixo,
                "chave": raw,
                "aviso": "Copie agora. A chave completa não será exibida de novo.",
            },
            status=status.HTTP_201_CREATED,
        )


class WhatsappParceiroChaveRevogarView(APIView):
    permission_classes = [IsSuperAdmin]

    def post(self, request, customer_id: int, key_id: int):
        key = WhatsappApiKey.objects.filter(id=key_id, customer_id=customer_id).first()
        if not key:
            return Response({"error": "Chave não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        if not key.revoked_at:
            key.revoked_at = timezone.now()
            key.save(update_fields=["revoked_at"])
        return Response({"ok": True, "id": key.id, "revogada": True})
