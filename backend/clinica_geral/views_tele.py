"""Página pública da teleconsulta — o paciente entra sem login."""
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .tele_service import obter_sala_publica


@method_decorator(csrf_exempt, name="dispatch")
class TeleconsultaPublicaView(View):
    def get(self, request, token):
        dados, err = obter_sala_publica(token)
        if err:
            return JsonResponse({"error": err}, status=400)
        return JsonResponse(dados)
