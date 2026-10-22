"""Importa PDF de produtos e serviços da prestadora para uma categoria do CRM."""
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from tenants.middleware import get_current_loja_id

from .catalogo_import_service import importar_catalogo_na_categoria
from .catalogo_pdf import CatalogoPdfError, preview_catalogo_pdf
from .vendedor_permissoes_service import verificar_permissao_crm_action


def _loja_id():
    loja_id = get_current_loja_id()
    if not loja_id:
        return None
    return loja_id


class CatalogoPdfPreviewView(APIView):
    """POST /crm-vendas/produtos-servicos/importar-pdf/ — lê o PDF e devolve a prévia."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        negado = verificar_permissao_crm_action(request, "produtoservico", "create")
        if negado is not None:
            return negado
        if not _loja_id():
            return Response({"detail": "Loja não identificada."}, status=400)
        arquivo = request.FILES.get("arquivo") or request.FILES.get("file")
        if arquivo is None:
            return Response({"detail": "Envie o PDF da tabela."}, status=400)
        nome = (arquivo.name or "").lower()
        if arquivo.content_type not in ("application/pdf", "application/octet-stream") and not nome.endswith(".pdf"):
            return Response({"detail": "Envie um arquivo PDF."}, status=400)
        try:
            return Response(preview_catalogo_pdf(arquivo.read()))
        except CatalogoPdfError as exc:
            return Response({"detail": str(exc)}, status=400)


class CatalogoPdfImportarView(APIView):
    """POST /crm-vendas/produtos-servicos/importar-pdf/confirmar/ — grava no catálogo da prestadora."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        negado = verificar_permissao_crm_action(request, "produtoservico", "create")
        if negado is not None:
            return negado
        loja_id = _loja_id()
        if not loja_id:
            return Response({"detail": "Loja não identificada."}, status=400)
        substituir = request.data.get("substituir") in (True, "true", "True", "1", 1)
        try:
            prestadora_id = int(request.data.get("prestadora_id"))
        except (TypeError, ValueError):
            return Response({"detail": "Escolha a prestadora dona deste catálogo."}, status=400)
        categoria_id = request.data.get("categoria_id") or None
        if categoria_id not in (None, ""):
            try:
                categoria_id = int(categoria_id)
            except (TypeError, ValueError):
                return Response({"detail": "Categoria inválida."}, status=400)
        else:
            categoria_id = None
        try:
            resultado = importar_catalogo_na_categoria(
                loja_id,
                request.data.get("itens") or [],
                prestadora_id,
                categoria_id=categoria_id,
                substituir=substituir,
            )
        except CatalogoPdfError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(resultado)
