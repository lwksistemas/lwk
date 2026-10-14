"""Revisão de português do texto ditado na anamnese e na evolução."""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import CLINICA_CLINICAL
from .texto_clinico_service import (
    TextoClinicoErro,
    TextoClinicoIndisponivel,
    revisar_texto_clinico,
)

_LIMITE = 8000


class RevisarTextoClinicoView(APIView):
    """POST /clinica-beleza/texto/revisar/"""

    permission_classes = CLINICA_CLINICAL

    def post(self, request):
        texto = str(request.data.get("texto") or "").strip()
        campo = str(request.data.get("campo") or "").strip()
        if not texto:
            return Response(
                {"error": "Escreva ou dite o texto antes de revisar."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(texto) > _LIMITE:
            return Response(
                {"error": "O texto está longo demais para revisar de uma vez."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            revisado = revisar_texto_clinico(texto, campo)
        except TextoClinicoIndisponivel as exc:
            return Response({"error": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except TextoClinicoErro as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        return Response({"texto": revisado})
