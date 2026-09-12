"""Views de fornecedor e catálogo — Clínica da Beleza."""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .fornecedor_service import FornecedorError, importar_catalogo, preview_catalogo_entrada, salvar_fornecedor
from .models.fornecedores import Fornecedor, FornecedorProduto
from .permissions import CLINICA_ESTOQUE, CLINICA_ESTOQUE_LEITURA
from .serializers.fornecedores import FornecedorProdutoSerializer, FornecedorSerializer
from .views_base import GetObjectMixin, resolve_loja_id_from_request


def _ensure(request):
    from tenants.middleware import ensure_loja_context
    ensure_loja_context(request)
    return resolve_loja_id_from_request(request)


def _erro(exc):
    return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class FornecedorListView(APIView):
    """GET/POST /clinica-beleza/estoque/fornecedores/"""

    permission_classes = CLINICA_ESTOQUE

    def get_permissions(self):
        if self.request.method == "GET":
            return [perm() for perm in CLINICA_ESTOQUE_LEITURA]
        return [perm() for perm in CLINICA_ESTOQUE]

    def get(self, request):
        loja_id = _ensure(request)
        qs = Fornecedor.objects.filter(loja_id=loja_id)
        if request.query_params.get("todos") not in ("1", "true", "True"):
            qs = qs.filter(is_active=True)
        q = (request.query_params.get("search") or "").strip()
        if q:
            from django.db.models import Q
            qs = qs.filter(
                Q(razao_social__icontains=q) | Q(nome_fantasia__icontains=q) | Q(cnpj__icontains=q)
            )
        return Response(FornecedorSerializer(qs, many=True).data)

    def post(self, request):
        loja_id = _ensure(request)
        try:
            obj = salvar_fornecedor(loja_id, request.data)
        except FornecedorError as exc:
            return _erro(exc)
        return Response(FornecedorSerializer(obj).data, status=status.HTTP_201_CREATED)


class FornecedorDetailView(GetObjectMixin, APIView):
    """GET/PUT/DELETE /clinica-beleza/estoque/fornecedores/<id>/"""

    permission_classes = CLINICA_ESTOQUE
    model_class = Fornecedor
    not_found_message = "Fornecedor não encontrado"

    def get_permissions(self):
        if self.request.method == "GET":
            return [perm() for perm in CLINICA_ESTOQUE_LEITURA]
        return [perm() for perm in CLINICA_ESTOQUE]

    def get(self, request, pk):
        _ensure(request)
        obj, error = self.object_or_404(pk)
        if error:
            return error
        return Response(FornecedorSerializer(obj).data)

    def put(self, request, pk):
        loja_id = _ensure(request)
        obj, error = self.object_or_404(pk)
        if error:
            return error
        try:
            obj = salvar_fornecedor(loja_id, request.data, fornecedor=obj)
        except FornecedorError as exc:
            return _erro(exc)
        return Response(FornecedorSerializer(obj).data)

    def delete(self, request, pk):
        _ensure(request)
        obj, error = self.object_or_404(pk)
        if error:
            return error
        if obj.pedidos.exists():
            obj.is_active = False
            obj.save(update_fields=["is_active", "updated_at"])
            return Response(FornecedorSerializer(obj).data)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FornecedorProdutoListView(APIView):
    """GET /clinica-beleza/estoque/fornecedores/<id>/produtos/"""

    permission_classes = CLINICA_ESTOQUE_LEITURA

    def get(self, request, pk):
        _ensure(request)
        forn = Fornecedor.objects.filter(pk=pk).first()
        if not forn:
            return Response({"error": "Fornecedor não encontrado"}, status=status.HTTP_404_NOT_FOUND)
        qs = FornecedorProduto.objects.filter(fornecedor=forn)
        q = (request.query_params.get("search") or "").strip()
        if q:
            from django.db.models import Q
            qs = qs.filter(Q(codigo__icontains=q) | Q(nome__icontains=q))
        return Response(FornecedorProdutoSerializer(qs[:80], many=True).data)


class FornecedorCatalogoPreviewView(APIView):
    """POST /clinica-beleza/estoque/fornecedores/<id>/catalogo/preview/"""

    permission_classes = CLINICA_ESTOQUE
    model_class = Fornecedor

    def post(self, request, pk):
        _ensure(request)
        if not Fornecedor.objects.filter(pk=pk).exists():
            return Response({"error": "Fornecedor não encontrado"}, status=status.HTTP_404_NOT_FOUND)
        try:
            itens = preview_catalogo_entrada(
                conteudo=request.data.get("conteudo"),
                arquivo=request.FILES.get("arquivo"),
            )
        except FornecedorError as exc:
            return _erro(exc)
        return Response({"itens": itens, "total": len(itens)})


class FornecedorCatalogoImportarView(APIView):
    """POST /clinica-beleza/estoque/fornecedores/<id>/catalogo/importar/"""

    permission_classes = CLINICA_ESTOQUE

    def post(self, request, pk):
        _ensure(request)
        forn = Fornecedor.objects.filter(pk=pk).first()
        if not forn:
            return Response({"error": "Fornecedor não encontrado"}, status=status.HTTP_404_NOT_FOUND)
        itens = request.data.get("itens")
        if not itens:
            try:
                itens = preview_catalogo_entrada(
                    conteudo=request.data.get("conteudo"),
                    arquivo=request.FILES.get("arquivo"),
                )
            except FornecedorError as exc:
                return _erro(exc)
        try:
            resultado = importar_catalogo(forn, itens)
        except FornecedorError as exc:
            return _erro(exc)
        return Response(resultado)
