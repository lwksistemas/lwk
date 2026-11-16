"""O WhatsApp busca o PDF por um endereço temporário. O token não revela outra loja."""
import secrets

from django.core.cache import cache
from django.http import HttpResponse
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

_CHAVE = "salao-recibo-pdf:"


def publicar_pdf(pdf: bytes) -> str:
    from django.conf import settings

    token = secrets.token_urlsafe(24)
    cache.set(_CHAVE + token, pdf, timeout=6 * 3600)
    base = getattr(settings, "API_BASE_URL", "") or "https://api.lwksistemas.com.br"
    return f"{base.rstrip('/')}/api/salao-cabeleireiro/recibos/{token}/"


class ReciboPublicoView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, token):
        pdf = cache.get(_CHAVE + token)
        if not isinstance(pdf, (bytes, bytearray)):
            return HttpResponse(status=404)
        resposta = HttpResponse(bytes(pdf), content_type="application/pdf")
        resposta["Content-Disposition"] = 'inline; filename="comprovante.pdf"'
        return resposta
