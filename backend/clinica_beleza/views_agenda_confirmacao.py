"""Views públicas — confirmação/cancelamento de agendamento pelo paciente.
"""
import json
import logging

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .agenda_confirmacao_service import (
    obter_dados_confirmacao,
    processar_resposta_confirmacao,
)

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class ConfirmarAgendamentoPublicaView(View):
    """GET/POST /api/clinica-beleza/confirmar-agendamento/{token}/
    """

    def dispatch(self, request, *args, **kwargs):
        from django.http import JsonResponse

        from .throttles import check_rate_limit
        if not check_rate_limit(request, "public_confirmacao", "30/min"):
            return JsonResponse({"error": "Muitas tentativas. Aguarde alguns segundos e tente novamente."}, status=429)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, token):
        dados, err, _ = obter_dados_confirmacao(token)
        if err:
            return JsonResponse({"error": err}, status=400)
        return JsonResponse(dados)

    def post(self, request, token):
        acao = ""
        if request.content_type and "json" in request.content_type:
            try:
                body = json.loads(request.body.decode("utf-8") or "{}")
                acao = body.get("acao") or body.get("action") or ""
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
        if not acao:
            acao = request.POST.get("acao") or request.POST.get("action") or ""

        result = processar_resposta_confirmacao(token, acao)
        if not result.ok:
            return JsonResponse({"error": result.message, "status": result.status}, status=400)

        status_display = None
        if result.status and result.appointment_id:
            from .agenda_confirmacao_service import decodificar_token_confirmacao

            payload = decodificar_token_confirmacao(token)
            modulo = (payload or {}).get("modulo") or "clinica_beleza"
            if modulo == "cabeleireiro":
                from cabeleireiro.models import Agendamento

                ag = Agendamento.objects.filter(pk=result.appointment_id).first()
                if ag:
                    status_display = ag.get_status_display()
            else:
                from .models import Appointment

                appt = Appointment.objects.filter(pk=result.appointment_id).first()
                if appt:
                    status_display = appt.get_status_display()

        return JsonResponse({
            "ok": True,
            "message": result.message,
            "status": result.status,
            "status_display": status_display,
            "already_done": result.already_done,
        })
