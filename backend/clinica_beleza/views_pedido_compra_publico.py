"""Página pública de assinatura do pedido de compra pelo fornecedor."""
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from core.assinatura_service import decodificar_token, normalizar_token_url

from .consentimento_assinatura_publica_service import configurar_tenant_publico_clinica
from .pedido_compra_service import (
    PedidoCompraError,
    assinar_fornecedor,
    buscar_assinatura_fornecedor_por_token,
    pdf_bytes_pedido,
    serializar_pedido,
)


def _rate_limit(request):
    from .throttles import check_rate_limit

    if not check_rate_limit(request, "public_assinatura", "30/min"):
        return JsonResponse(
            {"error": "Muitas tentativas. Aguarde alguns segundos e tente novamente."},
            status=429,
        )
    return None


def _ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()[:45]
    return request.META.get("REMOTE_ADDR", "0.0.0.0") or "0.0.0.0"


def _carregar(token: str):
    token = normalizar_token_url(token)
    payload = decodificar_token(token)
    if not payload or not payload.get("loja_id"):
        return None, JsonResponse({"error": "Link inválido."}, status=400)
    err = configurar_tenant_publico_clinica(payload["loja_id"])
    if err:
        return None, JsonResponse({"error": err}, status=400)
    ass = buscar_assinatura_fornecedor_por_token(token)
    if not ass:
        return None, JsonResponse({"error": "Link inválido ou expirado."}, status=400)
    return (payload, ass), None


@method_decorator(csrf_exempt, name="dispatch")
class PedidoCompraAssinaturaPublicaView(View):
    """GET/POST /api/clinica-beleza/assinar-pedido/{token}/"""

    def dispatch(self, request, *args, **kwargs):
        limited = _rate_limit(request)
        if limited:
            return limited
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, token):
        ctx, err = _carregar(token)
        if err:
            return err
        _payload, ass = ctx
        pedido = ass.pedido
        data = serializar_pedido(pedido)
        loja = data.get("loja") or {}
        data.update({
            "tipo_documento": "pedido_compra",
            "loja_nome": loja.get("nome") or "",
            "nome_assinante": ass.nome_assinante or pedido.fornecedor.razao_social,
            "ja_assinado": bool(ass.assinado),
        })
        return JsonResponse(data)

    def post(self, request, token):
        import json
        ctx, err = _carregar(token)
        if err:
            return err
        _payload, ass = ctx
        if ass.assinado:
            return JsonResponse({"error": "Este pedido já foi assinado."}, status=400)
        try:
            body = json.loads(request.body or b"{}")
        except json.JSONDecodeError:
            body = {}
        nome = (body.get("nome") or body.get("nome_assinante") or "").strip()
        try:
            pedido = assinar_fornecedor(token, nome, _ip(request))
        except PedidoCompraError as exc:
            return JsonResponse({"error": str(exc)}, status=400)
        return JsonResponse({
            "ok": True,
            "message": "Pedido assinado com sucesso.",
            "pedido": serializar_pedido(pedido),
        })


@method_decorator(csrf_exempt, name="dispatch")
class PedidoCompraAssinaturaPdfPublicaView(View):
    """GET /api/clinica-beleza/assinar-pedido/{token}/pdf/"""

    def dispatch(self, request, *args, **kwargs):
        limited = _rate_limit(request)
        if limited:
            return limited
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, token):
        ctx, err = _carregar(token)
        if err:
            return err
        _payload, ass = ctx
        pdf = pdf_bytes_pedido(ass.pedido)
        resp = HttpResponse(pdf, content_type="application/pdf")
        disposition = "attachment" if request.GET.get("download") == "1" else "inline"
        resp["Content-Disposition"] = f'{disposition}; filename="pedido_compra_{ass.pedido.numero}.pdf"'
        return resp
