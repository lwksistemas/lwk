"""Venda de produtos no balcão. Não abre atendimento."""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import CLINICA_ESTOQUE
from .venda_produto_service import VendaProdutoError, cancelar_venda_balcao, registrar_venda_balcao
from .views_base import resolve_loja_id_from_request


class VendaProdutoListView(APIView):
    permission_classes = CLINICA_ESTOQUE

    def post(self, request):
        loja_id = resolve_loja_id_from_request(request)
        if not loja_id:
            return Response({"error": "Loja não identificada."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            venda = registrar_venda_balcao(
                loja_id=loja_id,
                paciente=request.data.get("paciente"),
                itens=request.data.get("itens") or [],
                payment_method=request.data.get("payment_method") or "CASH",
            )
        except VendaProdutoError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {
                "id": venda.id,
                "payment_id": venda.payment_id,
                "total": str(venda.payment.valor_total),
                "status": venda.status,
            },
            status=status.HTTP_201_CREATED,
        )


class VendaProdutoCancelarView(APIView):
    permission_classes = CLINICA_ESTOQUE

    def post(self, request, pk):
        from .models import VendaBalcao

        loja_id = resolve_loja_id_from_request(request)
        venda = VendaBalcao.objects.filter(pk=pk, loja_id=loja_id).select_related("payment").first()
        if venda is None:
            return Response({"error": "Venda não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        try:
            cancelar_venda_balcao(venda)
        except VendaProdutoError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"id": venda.id, "status": venda.status})
