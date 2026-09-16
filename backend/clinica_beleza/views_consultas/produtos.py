"""Produtos utilizados na consulta (baixa de estoque ao finalizar)."""
from decimal import Decimal

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Consulta, ConsultaProdutoUtilizado, ProdutoEstoque
from ..permissions import CLINICA_CLINICAL
from ..serializers import ConsultaProdutoUtilizadoSerializer
from ..views_base import GetObjectMixin


class ConsultaProdutoListView(GetObjectMixin, APIView):
    """GET  /clinica-beleza/consultas/<consulta_id>/produtos/
    POST /clinica-beleza/consultas/<consulta_id>/produtos/
    """

    permission_classes = CLINICA_CLINICAL
    model_class = Consulta
    not_found_message = "Consulta não encontrada"

    def get(self, request, consulta_id):
        consulta, error = self.object_or_404(consulta_id)
        if error:
            return error
        qs = ConsultaProdutoUtilizado.objects.filter(
            consulta=consulta,
        ).select_related("produto").order_by("created_at")
        return Response(ConsultaProdutoUtilizadoSerializer(qs, many=True).data)

    def post(self, request, consulta_id):
        consulta, error = self.object_or_404(consulta_id)
        if error:
            return error
        if consulta.status != "IN_PROGRESS":
            return Response(
                {"error": "Só é possível registrar produtos com a consulta em atendimento."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        produto_id = request.data.get("produto")
        if not produto_id:
            return Response({"error": "Informe o produto."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            produto = ProdutoEstoque.objects.get(pk=produto_id, is_active=True)
        except ProdutoEstoque.DoesNotExist:
            return Response({"error": "Produto não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        try:
            quantidade = Decimal(str(request.data.get("quantidade", 0)))
            if quantidade <= 0:
                raise ValueError
        except Exception:
            return Response({"error": "Quantidade inválida."}, status=status.HTTP_400_BAD_REQUEST)

        lote = (request.data.get("lote") or produto.lote or "").strip()
        validade = request.data.get("validade") or produto.validade

        data = {
            "consulta": consulta.id,
            "produto": produto.id,
            "quantidade": quantidade,
            "lote": lote,
            "validade": validade or None,
        }
        serializer = ConsultaProdutoUtilizadoSerializer(data=data)
        if serializer.is_valid():
            obj = serializer.save(loja_id=consulta.loja_id)
            obj = ConsultaProdutoUtilizado.objects.select_related("produto").get(pk=obj.pk)
            return Response(
                ConsultaProdutoUtilizadoSerializer(obj).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConsultaProdutoDetailView(GetObjectMixin, APIView):
    """DELETE /clinica-beleza/consultas/<consulta_id>/produtos/<pk>/"""

    permission_classes = CLINICA_CLINICAL
    model_class = ConsultaProdutoUtilizado
    not_found_message = "Registro não encontrado."
    select_related_fields = ("consulta", "produto")

    def delete(self, request, consulta_id, pk):
        item, error = self.object_or_404(pk)
        if error:
            return error
        if item.consulta_id != consulta_id:
            return Response({"error": "Registro não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        consulta = item.consulta
        if consulta.status != "IN_PROGRESS":
            return Response(
                {"error": "Não é possível remover produtos após finalizar a consulta."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if item.estoque_baixado:
            return Response(
                {"error": "Produto já baixado do estoque."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
