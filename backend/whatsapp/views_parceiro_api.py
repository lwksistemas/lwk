"""API pública autenticada por chave de parceiro (não expõe a Evolution)."""
from __future__ import annotations

import json
import logging

from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from superadmin.services.whatsapp_painel_service import buscar_chave
from whatsapp.evolution_client import EvolutionAPIError, partner_evolution_configured
from whatsapp.parceiro_gateway_service import (
    aplicar_conexao_parceiro,
    atualizar_webhook_parceiro,
    conectar_numero,
    desconectar_numero,
    encaminhar_evento_parceiro,
    enviar_texto_parceiro,
    listar_numeros,
    status_numero,
)
from whatsapp.views_evolution_webhook import _parse_webhook_payload

logger = logging.getLogger(__name__)


def _bearer_token(request) -> str:
    header = request.META.get("HTTP_AUTHORIZATION") or ""
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return (request.headers.get("X-Api-Key") or "").strip()


def _chave_request(request):
    key = buscar_chave(_bearer_token(request))
    if not key:
        return None
    key.last_used_at = timezone.now()
    key.save(update_fields=["last_used_at"])
    return key


class _ParceiroAuthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def parceiro(self, request):
        key = _chave_request(request)
        if not key:
            return None, Response({"error": "Chave inválida ou revogada."}, status=status.HTTP_401_UNAUTHORIZED)
        return key.customer, None


def _erro_gateway(exc: Exception):
    if isinstance(exc, ValueError):
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    if isinstance(exc, EvolutionAPIError):
        return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
    logger.exception("Gateway parceiro: %s", exc)
    return Response({"error": "Falha no gateway WhatsApp."}, status=status.HTTP_502_BAD_GATEWAY)


class WhatsappParceiroMeView(_ParceiroAuthView):
    def get(self, request):
        customer, err = self.parceiro(request)
        if err:
            return err
        return Response(
            {
                "customer_id": customer.id,
                "nome": customer.nome,
                "documento": customer.documento,
                "tipo": customer.tipo,
                "quota_numeros": customer.quota_numeros,
                "webhook_url": customer.webhook_url,
                "ativo": customer.is_active,
                "gateway": "lwk",
                "evolution": partner_evolution_configured(),
                "endpoints": {
                    "me": "/api/whatsapp/v1/me/",
                    "numeros": "/api/whatsapp/v1/numeros/",
                    "mensagens": "/api/whatsapp/v1/mensagens/",
                },
            }
        )

    def post(self, request):
        customer, err = self.parceiro(request)
        if err:
            return err
        if "webhook_url" in request.data:
            try:
                atualizar_webhook_parceiro(customer, request.data.get("webhook_url") or "")
            except ValueError as exc:
                return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return self.get(request)


class WhatsappParceiroNumerosView(_ParceiroAuthView):
    def get(self, request):
        customer, err = self.parceiro(request)
        if err:
            return err
        try:
            return Response({"numeros": listar_numeros(customer)})
        except Exception as exc:
            return _erro_gateway(exc)

    def post(self, request):
        customer, err = self.parceiro(request)
        if err:
            return err
        cliente_id = (request.data.get("cliente_id") or request.data.get("id") or "").strip()
        rotulo = (request.data.get("rotulo") or request.data.get("nome") or "").strip()
        if not cliente_id:
            return Response({"error": "Informe cliente_id (id do cliente no sistema PHP)."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            data = conectar_numero(customer, cliente_id=cliente_id, rotulo=rotulo)
        except Exception as exc:
            return _erro_gateway(exc)
        return Response(data, status=status.HTTP_201_CREATED)


class WhatsappParceiroNumeroView(_ParceiroAuthView):
    def get(self, request, instance_name: str):
        customer, err = self.parceiro(request)
        if err:
            return err
        try:
            return Response(status_numero(customer, instance_name))
        except Exception as exc:
            return _erro_gateway(exc)


class WhatsappParceiroNumeroQrView(_ParceiroAuthView):
    def post(self, request, instance_name: str):
        customer, err = self.parceiro(request)
        if err:
            return err
        suffix = instance_name.split("_", 2)
        cliente_id = suffix[2] if len(suffix) >= 3 else instance_name
        try:
            data = conectar_numero(customer, cliente_id=cliente_id, rotulo=request.data.get("rotulo") or "")
        except Exception as exc:
            return _erro_gateway(exc)
        return Response(data)


class WhatsappParceiroNumeroDesconectarView(_ParceiroAuthView):
    def post(self, request, instance_name: str):
        customer, err = self.parceiro(request)
        if err:
            return err
        try:
            return Response(desconectar_numero(customer, instance_name))
        except Exception as exc:
            return _erro_gateway(exc)


class WhatsappParceiroMensagensView(_ParceiroAuthView):
    def post(self, request):
        customer, err = self.parceiro(request)
        if err:
            return err
        try:
            data = enviar_texto_parceiro(
                customer,
                request.data.get("instance") or request.data.get("instance_name") or "",
                request.data.get("number") or request.data.get("telefone") or "",
                request.data.get("text") or request.data.get("mensagem") or "",
            )
        except Exception as exc:
            return _erro_gateway(exc)
        return Response(data, status=status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name="dispatch")
class WhatsappParceiroEvolutionWebhookView(View):
    """POST /api/whatsapp/v1/webhook/ — Evolution da VM, não o PHP."""

    def get(self, request):
        return JsonResponse({"status": "ok", "service": "whatsapp-parceiro-webhook"})

    def post(self, request):
        if not self._authenticate(request):
            return HttpResponse("Unauthorized", status=401)
        try:
            body = json.loads(request.body.decode("utf-8") or "{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            return HttpResponse("OK", status=200)
        for event in _parse_webhook_payload(body):
            self._handle(event)
        return HttpResponse("OK", status=200)

    def _authenticate(self, request) -> bool:
        from django.conf import settings

        expected = (getattr(settings, "EVOLUTION_PARCEIRO_API_KEY", None) or "").strip()
        if not expected:
            return bool(getattr(settings, "DEBUG", False))
        received = (
            request.headers.get("Apikey")
            or request.headers.get("X-Api-Key")
            or request.META.get("HTTP_APIKEY", "")
        ).strip()
        if not received:
            try:
                body = json.loads(request.body.decode("utf-8") or "{}")
                if isinstance(body, dict):
                    received = (body.get("apikey") or "").strip()
            except (json.JSONDecodeError, UnicodeDecodeError):
                received = ""
        return received == expected

    def _handle(self, event: dict):
        instance = (event.get("instance") or "").strip()
        if not instance.lower().startswith("ext_"):
            logger.debug("Webhook parceiro: instance ignorada %s", instance)
            return
        event_name = (event.get("event") or "").lower().replace("_", ".")
        data = event.get("data") if isinstance(event.get("data"), dict) else {}
        try:
            if event_name == "connection.update":
                aplicar_conexao_parceiro(instance, data)
            encaminhar_evento_parceiro(instance, event)
        except Exception as exc:
            logger.exception("Webhook parceiro %s: %s", instance, exc)
