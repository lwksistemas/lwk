"""Middleware de fallback CORS para garantir headers em respostas da API.
Corrige erro "No 'Access-Control-Allow-Origin' header" em produção (Heroku, Render, Vercel).
"""
from django.conf import settings
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin


class CorsFallbackMiddleware(MiddlewareMixin):
    """Garante que respostas /api/ tenham headers CORS quando o Origin for permitido.
    Fallback para quando corsheaders não adiciona os headers (ex: erros 401/500).
    Também responde OPTIONS (preflight) para /api/ quando Origin é permitido.
    """

    SECURITY_HEADERS = {
        "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=(), browsing-topics=()",
    }
    NO_STORE_HEADERS = {
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
    }

    def process_request(self, request):
        """Responde OPTIONS (preflight) com headers CORS para /api/"""
        if request.method != "OPTIONS" or not request.path.startswith("/api/"):
            return None

        origin = request.META.get("HTTP_ORIGIN")
        if not origin:
            return None

        allowed = getattr(settings, "CORS_ALLOWED_ORIGINS", [])
        if not isinstance(allowed, (list, tuple)):
            allowed = []
        if origin not in allowed:
            return None

        response = HttpResponse(status=200)
        response["Access-Control-Allow-Origin"] = origin
        response["Access-Control-Allow-Credentials"] = "true"
        response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response["Access-Control-Allow-Headers"] = (
            "Accept, Authorization, Content-Type, X-Loja-ID, X-Tenant-Slug, X-Session-ID"
        )
        response["Access-Control-Max-Age"] = "86400"
        for key, value in self.SECURITY_HEADERS.items():
            response.setdefault(key, value)
        for key, value in self.NO_STORE_HEADERS.items():
            response.setdefault(key, value)
        return response

    def process_response(self, request, response):
        if not request.path.startswith("/api/"):
            return response

        for key, value in self.SECURITY_HEADERS.items():
            response.setdefault(key, value)
        for key, value in self.NO_STORE_HEADERS.items():
            response.setdefault(key, value)

        origin = request.META.get("HTTP_ORIGIN")
        if not origin:
            return response

        allowed = getattr(settings, "CORS_ALLOWED_ORIGINS", [])
        if not isinstance(allowed, (list, tuple)):
            allowed = []
        if origin not in allowed:
            return response

        # Se já tem o header, não sobrescrever
        if response.get("Access-Control-Allow-Origin"):
            return response

        response["Access-Control-Allow-Origin"] = origin
        response["Access-Control-Allow-Credentials"] = "true"
        response["Access-Control-Expose-Headers"] = "Content-Type, Authorization"
        return response
