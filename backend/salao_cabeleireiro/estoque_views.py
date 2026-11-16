"""Cadastro de produto e venda do caixa. A nota fiscal não é emitida aqui."""
from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .caixa_service import quantia
from .estoque_service import (
    gravar,
    nome_comercial,
    nome_fornecedor,
    publico_produto,
    publico_venda,
    registrar_venda,
    tenant_atomic,
)
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
            qs = qs.filter(Q(nome__icontains=termo) | Q(fornecedor__icontains=termo) | Q(codigo_barras__iexact=termo))
        return Response([publico_produto(item) for item in qs[:200]])

    def post(self, request):
        nome = nome_comercial(request.data.get("nome") or "")
        if len(nome) < 2:
            return _erro("Informe o nome comercial do produto.")
        fornecedor = nome_fornecedor(request.data.get("fornecedor") or "")
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
        with tenant_atomic():
            produto = gravar(
                Produto,
                nome=nome,
                fornecedor=fornecedor,
                codigo_barras=codigo,
                preco=preco,
                saldo=saldo,
                comissao_percentual=comissao,
            )
            if saldo:
                gravar(
                    MovimentoEstoque,
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
        nome = nome_comercial(request.data.get("nome") if "nome" in request.data else produto.nome)
        if len(nome) < 2:
            return _erro("Informe o nome comercial do produto.")
        fornecedor = nome_fornecedor(request.data.get("fornecedor") if "fornecedor" in request.data else produto.fornecedor)
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
        with tenant_atomic():
            produto = Produto.objects.select_for_update().get(pk=produto.pk)
            diferenca = saldo - produto.saldo
            produto.nome = nome
            produto.fornecedor = fornecedor
            produto.codigo_barras = codigo
            produto.preco = preco
            produto.saldo = saldo
            produto.comissao_percentual = comissao
            produto.save()
            if diferenca:
                gravar(
                    MovimentoEstoque,
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


def _agendamentos_pedidos(dados):
    brutos = dados.get("agendamentos")
    if not isinstance(brutos, list):
        unico = dados.get("agendamento")
        brutos = [] if unico in (None, "", 0, "0") else [unico]
    ids = []
    for bruto in brutos:
        try:
            pk = int(bruto)
        except (TypeError, ValueError) as exc:
            raise ValueError("Agendamento não encontrado.") from exc
        if pk not in ids:
            ids.append(pk)
    itens = []
    for pk in ids:
        item = _agendamento_completo(pk)
        if item is None:
            raise ValueError("Agendamento não encontrado.")
        itens.append(item)
    return itens


class VendaListView(APIView):
    permission_classes = [IsAuthenticated, IsSalaoMembro]

    def get(self, request):
        from datetime import datetime, timedelta

        from django.utils import timezone
        from django.utils.dateparse import parse_date

        from .models import Venda

        qs = Venda.objects.all().order_by("-numero")
        termo = (request.query_params.get("q") or "").strip()
        dia = parse_date((request.query_params.get("data") or "").strip())
        if termo.isdigit():
            qs = qs.filter(numero=int(termo))
        elif termo:
            qs = qs.filter(cliente_nome__icontains=termo)
        if dia is not None:
            inicio = timezone.make_aware(datetime(dia.year, dia.month, dia.day))
            qs = qs.filter(created_at__gte=inicio, created_at__lt=inicio + timedelta(days=1))
        return Response([
            {
                "numero": item.numero,
                "quando": timezone.localtime(item.created_at).strftime("%d/%m/%Y %H:%M"),
                "cliente": item.cliente_nome or "Consumidor",
                "valor": f"{quantia(item.valor):.2f}",
                "operador": item.operador_nome or "",
                "cancelado": not item.is_active,
            }
            for item in qs[:80]
        ])


class VendaCreateView(APIView):
    permission_classes = [IsAuthenticated, IsSalaoMembro]

    def get(self, request):
        return VendaListView().get(request)

    def post(self, request):
        try:
            agendamentos = _agendamentos_pedidos(request.data)
        except ValueError as exc:
            return _erro(str(exc), status.HTTP_404_NOT_FOUND)
        config = _config()
        origem = (request.data.get("origem") or "caixa").strip()
        if origem not in {"agenda", "caixa"}:
            origem = "caixa"
        loja, prof = contexto_salao(request)
        try:
            usuario = request.user
            operador = (usuario.get_full_name() or "").strip() or usuario.get_username()
            venda = registrar_venda(
                request.data,
                agendamentos,
                papel_salao(loja, prof, request.user, config.modelo),
                config.local_recebimento,
                origem,
                operador,
            )
        except PermissionError as exc:
            return _erro(str(exc), status.HTTP_403_FORBIDDEN)
        except ValueError as exc:
            return _erro(str(exc))
        return Response(publico_venda(venda), status=status.HTTP_201_CREATED)


class VendaDetailView(APIView):
    permission_classes = [IsAuthenticated, IsSalaoMembro]

    def get(self, request, numero):
        from .models import Venda

        venda = Venda.objects.filter(numero=numero).prefetch_related("itens").first()
        if venda is None:
            return _erro("Comprovante não encontrado.", status.HTTP_404_NOT_FOUND)
        return Response(publico_venda(venda))


def _venda_numero(numero):
    from .models import Venda

    return Venda.objects.filter(numero=numero).prefetch_related("itens").first()


class VendaHtmlView(APIView):
    permission_classes = [IsAuthenticated, IsSalaoMembro]

    def get(self, request, numero):
        from django.http import HttpResponse

        from .comprovante_layout import comprovante_da_venda, html_comprovante

        venda = _venda_numero(numero)
        if venda is None:
            return _erro("Comprovante não encontrado.", status.HTTP_404_NOT_FOUND)
        return HttpResponse(html_comprovante(comprovante_da_venda(venda)), content_type="text/html; charset=utf-8")


class VendaPdfView(APIView):
    permission_classes = [IsAuthenticated, IsSalaoMembro]

    def get(self, request, numero):
        from django.http import HttpResponse

        from .comprovante_layout import comprovante_da_venda, pdf_comprovante

        venda = _venda_numero(numero)
        if venda is None:
            return _erro("Comprovante não encontrado.", status.HTTP_404_NOT_FOUND)
        pdf = pdf_comprovante(comprovante_da_venda(venda))
        resposta = HttpResponse(pdf, content_type="application/pdf")
        resposta["Content-Disposition"] = f'attachment; filename="comprovante-{int(numero):06d}.pdf"'
        return resposta


class VendaEnviarView(APIView):
    permission_classes = [IsAuthenticated, IsSalaoMembro]

    def post(self, request, numero):
        from .models import Venda
        from .recibo_envio import enviar_comprovante

        venda = Venda.objects.filter(numero=numero, is_active=True).prefetch_related("itens").first()
        if venda is None:
            return _erro("Comprovante não encontrado.", status.HTTP_404_NOT_FOUND)
        ok, mensagem = enviar_comprovante(venda, (request.data.get("canal") or "").strip(), user=request.user)
        if not ok:
            return _erro(mensagem)
        return Response({"success": True, "message": mensagem})
