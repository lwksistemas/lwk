"""Cadastro de produto e venda do caixa. A nota fiscal não é emitida aqui."""
from django.db import transaction
from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .caixa_service import quantia
from .estoque_service import publico_produto, publico_venda, registrar_venda
from .models import MovimentoEstoque, Produto
from .permissions import IsSalaoAdmin, IsSalaoMembro, contexto_salao, papel_salao
from .views import _agendamento_completo, _config, _erro


class ProdutoListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsSalaoAdmin()]
        return [IsAuthenticated(), IsSalaoMembro()]

    def get(self, request):
        qs = Produto.objects.filter(is_active=True).order_by("nome")
        termo = (request.query_params.get("q") or "").strip()
        if termo:
            qs = qs.filter(Q(nome__icontains=termo) | Q(codigo_barras__iexact=termo))
        return Response([publico_produto(item) for item in qs[:200]])

    def post(self, request):
        nome = (request.data.get("nome") or "").strip()
        if len(nome) < 2:
            return _erro("Informe o nome do produto.")
        try:
            preco = quantia(request.data.get("preco") or 0)
            saldo = int(request.data.get("saldo") or 0)
            comissao = quantia(request.data.get("comissao_percentual") or 0)
        except (TypeError, ValueError):
            return _erro("Informe preço, saldo e comissão válidos.")
        if preco < 0 or saldo < 0 or comissao < 0:
            return _erro("Preço, saldo e comissão não podem ser negativos.")
        codigo = (request.data.get("codigo_barras") or "").strip()[:40]
        if codigo and Produto.objects.filter(is_active=True, codigo_barras=codigo).exists():
            return _erro("Já existe um produto com este código.")
        with transaction.atomic():
            produto = Produto.objects.create(
                nome=nome[:120],
                codigo_barras=codigo,
                preco=preco,
                saldo=saldo,
                comissao_percentual=comissao,
            )
            if saldo:
                MovimentoEstoque.objects.create(
                    produto=produto,
                    tipo="entrada",
                    quantidade=saldo,
                    saldo_depois=saldo,
                )
        return Response(publico_produto(produto), status=status.HTTP_201_CREATED)


class ProdutoDetailView(APIView):
    permission_classes = [IsAuthenticated, IsSalaoAdmin]

    def patch(self, request, pk):
        produto = Produto.objects.filter(pk=pk, is_active=True).first()
        if produto is None:
            return _erro("Produto não encontrado.", status.HTTP_404_NOT_FOUND)
        nome = (request.data.get("nome") or produto.nome).strip()
        if len(nome) < 2:
            return _erro("Informe o nome do produto.")
        try:
            preco = quantia(request.data.get("preco") if request.data.get("preco") not in (None, "") else produto.preco)
            saldo = int(request.data.get("saldo") if request.data.get("saldo") not in (None, "") else produto.saldo)
            comissao = quantia(request.data.get("comissao_percentual") if "comissao_percentual" in request.data else produto.comissao_percentual)
        except (TypeError, ValueError):
            return _erro("Informe preço, saldo e comissão válidos.")
        if preco < 0 or saldo < 0 or comissao < 0:
            return _erro("Preço, saldo e comissão não podem ser negativos.")
        codigo = (request.data.get("codigo_barras") if "codigo_barras" in request.data else produto.codigo_barras) or ""
        codigo = str(codigo).strip()[:40]
        if codigo and Produto.objects.filter(is_active=True, codigo_barras=codigo).exclude(pk=produto.pk).exists():
            return _erro("Já existe um produto com este código.")
        with transaction.atomic():
            produto = Produto.objects.select_for_update().get(pk=produto.pk)
            diferenca = saldo - produto.saldo
            produto.nome = nome[:120]
            produto.codigo_barras = codigo
            produto.preco = preco
            produto.saldo = saldo
            produto.comissao_percentual = comissao
            produto.save()
            if diferenca:
                MovimentoEstoque.objects.create(
                    produto=produto,
                    tipo="ajuste",
                    quantidade=diferenca,
                    saldo_depois=saldo,
                )
        return Response(publico_produto(produto))

    def delete(self, request, pk):
        produto = Produto.objects.filter(pk=pk, is_active=True).first()
        if produto is None:
            return _erro("Produto não encontrado.", status.HTTP_404_NOT_FOUND)
        produto.is_active = False
        produto.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class VendaCreateView(APIView):
    permission_classes = [IsAuthenticated, IsSalaoMembro]

    def post(self, request):
        agendamento = None
        bruto = request.data.get("agendamento")
        if bruto not in (None, "", 0, "0"):
            try:
                agendamento = _agendamento_completo(int(bruto))
            except (TypeError, ValueError):
                agendamento = None
            if agendamento is None:
                return _erro("Agendamento não encontrado.", status.HTTP_404_NOT_FOUND)
        config = _config()
        origem = (request.data.get("origem") or "caixa").strip()
        if origem not in {"agenda", "caixa"}:
            origem = "caixa"
        loja, prof = contexto_salao(request)
        try:
            venda = registrar_venda(
                request.data,
                agendamento,
                papel_salao(loja, prof, request.user, config.modelo),
                config.local_recebimento,
                origem,
            )
        except PermissionError as exc:
            return _erro(str(exc), status.HTTP_403_FORBIDDEN)
        except ValueError as exc:
            return _erro(str(exc))
        return Response(publico_venda(venda), status=status.HTTP_201_CREATED)
