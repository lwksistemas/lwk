"""Ativar e usar o rosto no login. A foto do rosto não entra no servidor."""

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.auth_cookies import attach_auth_cookies
from core.throttling import AuthLoginThrottle
from superadmin.rosto_service import (
    RostoErro,
    confirmar_entrada,
    confirmar_registro,
    opcoes_entrada,
    opcoes_registro,
)


def _erro(exc: RostoErro) -> Response:
    return Response({"error": exc.mensagem}, status=exc.status)


def _tipo(request) -> tuple[str, str | None]:
    return (request.data.get("user_type") or "").strip(), (request.data.get("loja_slug") or "").strip() or None


class RostoRegistrarOpcoesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_type, loja_slug = _tipo(request)
        try:
            opcoes = opcoes_registro(request, request.user, user_type, loja_slug)
        except RostoErro as exc:
            return _erro(exc)
        return Response({"publicKey": opcoes})


class RostoRegistrarView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_type, loja_slug = _tipo(request)
        try:
            confirmar_registro(request, request.user, user_type, loja_slug, request.data.get("credential") or {})
        except RostoErro as exc:
            return _erro(exc)
        return Response({"ok": True})


class RostoEntrarOpcoesView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthLoginThrottle]

    def post(self, request):
        user_type, loja_slug = _tipo(request)
        try:
            opcoes = opcoes_entrada(request, request.data.get("username") or "", user_type, loja_slug)
        except RostoErro as exc:
            return _erro(exc)
        return Response({"publicKey": opcoes})


class RostoEntrarView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthLoginThrottle]

    def post(self, request):
        user_type, loja_slug = _tipo(request)
        try:
            resultado = confirmar_entrada(
                request,
                request.data.get("username") or "",
                user_type,
                loja_slug,
                request.data.get("credential") or {},
            )
        except RostoErro as exc:
            return _erro(exc)
        response = Response(resultado.data, status=resultado.status_code)
        if resultado.success and resultado.cookies:
            return attach_auth_cookies(
                response,
                access=resultado.cookies["access"],
                refresh=resultado.cookies["refresh"],
                session_id=resultado.cookies["session_id"],
            )
        return response
