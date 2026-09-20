"""Views da assinatura digital do recibo de pagamento.

Internas (autenticadas): status, enviar link, reenviar, download do PDF.
Públicas (paciente): página de assinatura (GET/POST) e PDF para leitura.
Reusa o motor genérico core.assinatura_service e o adapter ReciboAssinaturaAdapter.
"""
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payment
from .permissions import CLINICA_FINANCEIRO
from .recibo_assinatura_adapter import ReciboAssinaturaAdapter
from .recibo_assinatura_envio_service import (
    enviar_recibo_assinado,
    enviar_recibo_para_assinatura,
    normalizar_canal_envio,
)
from .views_base import GetObjectMixin

STATUS_DISPLAY_RECIBO = {
    "rascunho": "Rascunho",
    "aguardando_paciente": "Aguardando Paciente",
    "concluido": "Concluído",
}


# ---------------------------------------------------------------------------
# Views internas (autenticadas)
# ---------------------------------------------------------------------------
class ReciboAssinaturaStatusView(GetObjectMixin, APIView):
    """GET /clinica-beleza/payments/<id>/assinatura-recibo/ — status da assinatura."""

    permission_classes = CLINICA_FINANCEIRO
    model_class = Payment
    not_found_message = "Pagamento não encontrado"
    select_related_fields = ("appointment", "appointment__patient")

    def get(self, request, pk):
        payment, err = self.object_or_404(pk)
        if err:
            return err
        st = payment.status_assinatura_recibo or "rascunho"
        return Response({
            "status_assinatura": st,
            "status_assinatura_display": STATUS_DISPLAY_RECIBO.get(st, st),
        })


class ReciboAssinaturaEnviarView(GetObjectMixin, APIView):
    """POST /clinica-beleza/payments/<id>/assinatura-recibo/enviar/ — envia link para o paciente.

    Body: {"canal": "email" | "whatsapp"}.
    """

    permission_classes = CLINICA_FINANCEIRO
    model_class = Payment
    not_found_message = "Pagamento não encontrado"
    select_related_fields = ("appointment", "appointment__patient", "appointment__professional")

    def post(self, request, pk):
        payment, err = self.object_or_404(pk)
        if err:
            return err

        canal = normalizar_canal_envio(request.data.get("canal"))
        if not canal:
            return Response({"error": 'Canal deve ser "email" ou "whatsapp".'}, status=status.HTTP_400_BAD_REQUEST)

        # Assinatura do recibo é exclusiva de pagamento a prazo.
        if payment.payment_method != "PRAZO":
            return Response(
                {"error": "A assinatura do recibo está disponível apenas para pagamento a prazo."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Só faz sentido pedir assinatura de consulta já finalizada.
        consulta = getattr(payment.appointment, "consulta", None) if payment.appointment else None
        if consulta is not None and consulta.status != "COMPLETED":
            return Response(
                {"error": "Finalize a consulta antes de enviar o recibo para assinatura."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        adapter = ReciboAssinaturaAdapter()
        ok, msg = enviar_recibo_para_assinatura(
            payment=payment, adapter=adapter, loja_id=payment.loja_id, canal=canal, request=request,
        )
        if ok:
            return Response({"success": True, "message": msg})
        return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)


class ReciboAssinaturaPdfView(GetObjectMixin, APIView):
    """GET /clinica-beleza/payments/<id>/assinatura-recibo/pdf/ — download do PDF (assinado se houver)."""

    permission_classes = CLINICA_FINANCEIRO
    model_class = Payment
    not_found_message = "Pagamento não encontrado"
    select_related_fields = ("appointment", "appointment__patient", "appointment__professional")

    def get(self, request, pk):
        payment, err = self.object_or_404(pk)
        if err:
            return err
        adapter = ReciboAssinaturaAdapter()
        assinado = (payment.status_assinatura_recibo == "concluido")
        pdf = adapter.gerar_pdf(payment, incluir_assinaturas=assinado)
        response = HttpResponse(pdf.getvalue(), content_type="application/pdf")
        sufixo = "_assinado" if assinado else ""
        response["Content-Disposition"] = f'attachment; filename="recibo_{pk}{sufixo}.pdf"'
        return response


# ---------------------------------------------------------------------------
# Views públicas (paciente assina sem login)
# ---------------------------------------------------------------------------
def _rate_limit_recibo_publico(request):
    from .throttles import check_rate_limit

    if not check_rate_limit(request, "public_assinatura_recibo", "30/min"):
        return JsonResponse(
            {"error": "Muitas tentativas. Aguarde alguns segundos e tente novamente."},
            status=429,
        )
    return None


def _carregar_assinatura_recibo_publica(token):
    from core.assinatura_service import decodificar_token, normalizar_token_url

    from .consentimento_assinatura_publica_service import (
        configurar_tenant_publico_clinica,
        resolver_assinatura_publica,
    )

    token = normalizar_token_url(token)
    payload = decodificar_token(token)
    if not payload or not payload.get("loja_id"):
        return None, JsonResponse({"error": "Link inválido."}, status=400)

    err = configurar_tenant_publico_clinica(payload["loja_id"])
    if err:
        return None, JsonResponse({"error": err}, status=400)

    adapter = ReciboAssinaturaAdapter()
    _payload, assinatura, ass_err = resolver_assinatura_publica(adapter, token)
    if ass_err or not assinatura:
        return None, JsonResponse({"error": ass_err or "Link inválido."}, status=400)
    if assinatura.assinado:
        return None, JsonResponse({"error": "Este recibo já foi assinado."}, status=400)

    payment = adapter.get_documento_da_assinatura(assinatura)
    if not payment:
        return None, JsonResponse(
            {"error": "Recibo não encontrado. Solicite novo envio à clínica."},
            status=400,
        )
    return (payload, adapter, assinatura, payment), None


@method_decorator(csrf_exempt, name="dispatch")
class ReciboAssinaturaPublicaView(View):
    """GET/POST /api/clinica-beleza/assinar-recibo/<token>/"""

    def dispatch(self, request, *args, **kwargs):
        limited = _rate_limit_recibo_publico(request)
        if limited:
            return limited
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, token):
        ctx, err = _carregar_assinatura_recibo_publica(token)
        if err:
            return err
        _payload, adapter, assinatura, payment = ctx

        loja_nome = ""
        from superadmin.models import Loja

        loja = Loja.objects.using("default").filter(id=payment.loja_id).first()
        if loja:
            loja_nome = loja.nome

        appointment = getattr(payment, "appointment", None)
        patient = getattr(appointment, "patient", None) if appointment else None
        professional = getattr(appointment, "professional", None) if appointment else None

        return JsonResponse({
            "tipo_documento": "recibo_pagamento",
            "titulo": adapter.get_titulo(payment),
            "valor": adapter.get_valor_display(payment),
            "nome_assinante": assinatura.nome_assinante,
            "paciente_nome": getattr(patient, "nome", "") if patient else "",
            "profissional_nome": getattr(professional, "nome", "") if professional else "",
            "clinica_nome": loja_nome,
        })

    def post(self, request, token):
        from django.utils import timezone

        ctx, err = _carregar_assinatura_recibo_publica(token)
        if err:
            return err
        _payload, adapter, assinatura, payment = ctx
        loja_id = payment.loja_id

        ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "0.0.0.0"))
        if "," in ip:
            ip = ip.split(",")[0].strip()
        ua = request.META.get("HTTP_USER_AGENT", "")

        # Recibo tem uma única parte (paciente): marca a assinatura e conclui.
        assinatura.assinado = True
        assinatura.assinado_em = timezone.now()
        assinatura.ip_address = ip or "0.0.0.0"
        assinatura.user_agent = (ua or "")[:500]
        assinatura.save(update_fields=["assinado", "assinado_em", "ip_address", "user_agent", "updated_at"])

        adapter.atualizar_status_assinatura(payment, "concluido")
        adapter.on_assinatura_concluida(payment, loja_id)

        # Envia o recibo assinado por email e WhatsApp (não bloqueia a resposta ao paciente).
        from contextlib import suppress

        with suppress(Exception):
            enviar_recibo_assinado(
                payment=payment, adapter=adapter, loja_id=loja_id,
                user=request.user if request.user.is_authenticated else None,
            )

        return JsonResponse({
            "success": True,
            "proximo_status": "concluido",
            "proximo_status_display": STATUS_DISPLAY_RECIBO["concluido"],
        })


@method_decorator(csrf_exempt, name="dispatch")
class ReciboAssinaturaPdfPublicaView(View):
    """GET /api/clinica-beleza/assinar-recibo/<token>/pdf/ — PDF para o paciente ler antes de assinar."""

    def dispatch(self, request, *args, **kwargs):
        limited = _rate_limit_recibo_publico(request)
        if limited:
            return limited
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, token):
        ctx, err = _carregar_assinatura_recibo_publica(token)
        if err:
            return err
        _payload, adapter, _assinatura, payment = ctx
        pdf = adapter.gerar_pdf(payment, incluir_assinaturas=False)
        response = HttpResponse(pdf.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="recibo_{payment.id}.pdf"'
        return response
