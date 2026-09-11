"""Views autenticadas de pedido de compra."""
from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models.fornecedores import PedidoCompra
from .pedido_compra_service import (
    PedidoCompraError,
    atualizar_pedido,
    assinar_clinica,
    cancelar_pedido,
    criar_pedido,
    enviar_link_fornecedor,
    enviar_pedido_assinado,
    listar_profissionais_assinantes,
    pdf_bytes_pedido,
    pdf_publico_cache,
    serializar_pedido,
    _ip_request,
)
from .permissions import CLINICA_ESTOQUE, CLINICA_ESTOQUE_LEITURA
from .views_base import GetObjectMixin, resolve_loja_id_from_request


def _ensure(request):
    from tenants.middleware import ensure_loja_context
    ensure_loja_context(request)
    return resolve_loja_id_from_request(request)


def _erro(exc):
    return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


def _pedido_qs():
    return PedidoCompra.objects.select_related("fornecedor").prefetch_related("itens", "assinaturas")


class PedidoCompraAssinantesView(APIView):
    """GET /clinica-beleza/estoque/pedidos/assinantes/"""

    permission_classes = CLINICA_ESTOQUE_LEITURA

    def get(self, request):
        loja_id = _ensure(request)
        return Response(listar_profissionais_assinantes(loja_id))


class PedidoCompraListView(APIView):
    """GET/POST /clinica-beleza/estoque/pedidos/"""

    permission_classes = CLINICA_ESTOQUE

    def get_permissions(self):
        if self.request.method == "GET":
            return [perm() for perm in CLINICA_ESTOQUE_LEITURA]
        return [perm() for perm in CLINICA_ESTOQUE]

    def get(self, request):
        loja_id = _ensure(request)
        qs = _pedido_qs().filter(loja_id=loja_id)
        status_f = (request.query_params.get("status") or "").strip()
        if status_f:
            qs = qs.filter(status=status_f)
        return Response([serializar_pedido(p) for p in qs[:100]])

    def post(self, request):
        loja_id = _ensure(request)
        try:
            pedido = criar_pedido(loja_id, request.data)
        except PedidoCompraError as exc:
            return _erro(exc)
        pedido = _pedido_qs().get(pk=pedido.pk)
        return Response(serializar_pedido(pedido), status=status.HTTP_201_CREATED)


class PedidoCompraDetailView(GetObjectMixin, APIView):
    """GET/PUT /clinica-beleza/estoque/pedidos/<id>/"""

    permission_classes = CLINICA_ESTOQUE
    model_class = PedidoCompra
    not_found_message = "Pedido não encontrado"
    select_related_fields = ("fornecedor",)
    prefetch_related_fields = ("itens", "assinaturas")

    def get_permissions(self):
        if self.request.method == "GET":
            return [perm() for perm in CLINICA_ESTOQUE_LEITURA]
        return [perm() for perm in CLINICA_ESTOQUE]

    def get(self, request, pk):
        _ensure(request)
        obj, error = self.object_or_404(pk)
        if error:
            return error
        return Response(serializar_pedido(obj))

    def put(self, request, pk):
        _ensure(request)
        obj, error = self.object_or_404(pk)
        if error:
            return error
        try:
            atualizar_pedido(obj, request.data)
        except PedidoCompraError as exc:
            return _erro(exc)
        obj = _pedido_qs().get(pk=obj.pk)
        return Response(serializar_pedido(obj))


class PedidoCompraCancelarView(GetObjectMixin, APIView):
    permission_classes = CLINICA_ESTOQUE
    model_class = PedidoCompra
    not_found_message = "Pedido não encontrado"

    def post(self, request, pk):
        _ensure(request)
        obj, error = self.object_or_404(pk)
        if error:
            return error
        try:
            cancelar_pedido(obj)
        except PedidoCompraError as exc:
            return _erro(exc)
        obj = _pedido_qs().get(pk=obj.pk)
        return Response(serializar_pedido(obj))


class PedidoCompraAssinarClinicaView(GetObjectMixin, APIView):
    permission_classes = CLINICA_ESTOQUE
    model_class = PedidoCompra
    not_found_message = "Pedido não encontrado"
    select_related_fields = ("fornecedor",)
    prefetch_related_fields = ("itens", "assinaturas")

    def post(self, request, pk):
        _ensure(request)
        obj, error = self.object_or_404(pk)
        if error:
            return error
        nome = (request.data.get("nome") or request.data.get("nome_assinante") or "").strip()
        profissional_id = request.data.get("profissional_id") or request.data.get("profissional")
        try:
            assinar_clinica(obj, nome, _ip_request(request), profissional_id=profissional_id)
        except PedidoCompraError as exc:
            return _erro(exc)
        obj = _pedido_qs().get(pk=obj.pk)
        return Response(serializar_pedido(obj))


class PedidoCompraEnviarLinkView(GetObjectMixin, APIView):
    permission_classes = CLINICA_ESTOQUE
    model_class = PedidoCompra
    not_found_message = "Pedido não encontrado"
    select_related_fields = ("fornecedor",)

    def post(self, request, pk):
        _ensure(request)
        obj, error = self.object_or_404(pk)
        if error:
            return error
        canais = request.data.get("canais") or []
        if isinstance(canais, str):
            canais = [canais]
        canal = request.data.get("canal")
        if canal:
            canais = list(canais) + [canal]
        try:
            resultado = enviar_link_fornecedor(obj, canais)
        except PedidoCompraError as exc:
            return _erro(exc)
        obj = _pedido_qs().get(pk=obj.pk)
        return Response({"pedido": serializar_pedido(obj), **resultado})


class PedidoCompraEnviarView(GetObjectMixin, APIView):
    permission_classes = CLINICA_ESTOQUE
    model_class = PedidoCompra
    not_found_message = "Pedido não encontrado"
    select_related_fields = ("fornecedor",)
    prefetch_related_fields = ("itens", "assinaturas")

    def post(self, request, pk):
        _ensure(request)
        obj, error = self.object_or_404(pk)
        if error:
            return error
        canais = request.data.get("canais") or []
        if isinstance(canais, str):
            canais = [canais]
        canal = request.data.get("canal")
        if canal:
            canais = list(canais) + [canal]
        try:
            resultado = enviar_pedido_assinado(obj, canais)
        except PedidoCompraError as exc:
            return _erro(exc)
        obj = _pedido_qs().get(pk=obj.pk)
        return Response({"pedido": serializar_pedido(obj), **resultado})


class PedidoCompraPdfView(GetObjectMixin, APIView):
    permission_classes = CLINICA_ESTOQUE_LEITURA
    model_class = PedidoCompra
    not_found_message = "Pedido não encontrado"
    select_related_fields = ("fornecedor",)
    prefetch_related_fields = ("itens", "assinaturas")

    def get(self, request, pk):
        _ensure(request)
        obj, error = self.object_or_404(pk)
        if error:
            return error
        pdf = pdf_bytes_pedido(obj)
        resp = HttpResponse(pdf, content_type="application/pdf")
        resp["Content-Disposition"] = f'inline; filename="pedido_compra_{obj.numero}.pdf"'
        return resp


class PedidoCompraPdfPublicView(APIView):
    """GET público temporário para Evolution enviar o PDF no WhatsApp."""

    authentication_classes = []
    permission_classes = []

    def get(self, request, pk, token):
        pdf = pdf_publico_cache(int(pk), token)
        if not pdf:
            return Response({"error": "Link expirado."}, status=status.HTTP_404_NOT_FOUND)
        resp = HttpResponse(pdf, content_type="application/pdf")
        resp["Content-Disposition"] = f'inline; filename="pedido_compra_{pk}.pdf"'
        return resp
