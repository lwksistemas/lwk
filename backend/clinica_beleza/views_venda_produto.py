"""Venda de produtos no balcão. Não abre atendimento."""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import CLINICA_ESTOQUE
from .venda_produto_service import (
    VendaProdutoError,
    abrir_caixa,
    cancelar_venda_balcao,
    fechar_caixa,
    funcionarios_do_caixa,
    totais_gaveta,
    nome_exibicao_venda,
    registrar_venda_balcao,
    sessao_caixa_aberta,
    totais_sessao_caixa,
)
from .views_base import resolve_loja_id_from_request


def _venda_resumo(venda) -> dict:
    payment = venda.payment if venda.payment_id else None
    return {
        "id": venda.id,
        "payment_id": venda.payment_id,
        "total": str(payment.valor_total) if payment is not None else "0",
        "status": venda.status,
        "cliente": nome_exibicao_venda(venda),
        "telefone": (venda.telefone_cliente or getattr(getattr(venda, "paciente", None), "telefone", "") or ""),
        "email": (venda.email_cliente or getattr(getattr(venda, "paciente", None), "email", "") or ""),
        "operador": venda.operador_nome,
        "recibo_numero": venda.payment_id,
        "forma": payment.get_payment_method_display() if payment is not None else "",
        "criada_em": venda.created_at.isoformat() if venda.created_at else "",
    }


class VendaProdutoListView(APIView):
    permission_classes = CLINICA_ESTOQUE

    def get(self, request):
        from datetime import datetime, time

        from django.utils import timezone
        from django.utils.dateparse import parse_date

        from .models import VendaBalcao

        loja_id = resolve_loja_id_from_request(request)
        qs = VendaBalcao.objects.filter(loja_id=loja_id).select_related("payment", "paciente")
        dia = parse_date(str(request.query_params.get("data") or ""))
        if dia:
            qs = qs.filter(
                created_at__gte=timezone.make_aware(datetime.combine(dia, time.min)),
                created_at__lte=timezone.make_aware(datetime.combine(dia, time.max)),
            )
        return Response([_venda_resumo(venda) for venda in qs.order_by("-id")[:100]])

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
                nome_cliente=request.data.get("nome_cliente") or "",
                telefone_cliente=request.data.get("telefone") or "",
                email_cliente=request.data.get("email") or "",
                usuario=request.user,
                chave=request.data.get("chave") or "",
            )
        except VendaProdutoError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(_venda_resumo(venda), status=status.HTTP_201_CREATED)


class CaixaSessaoView(APIView):
    permission_classes = CLINICA_ESTOQUE

    def get(self, request):
        loja_id = resolve_loja_id_from_request(request)
        aberta = sessao_caixa_aberta(loja_id)
        corpo = {
            "aberta": aberta is not None,
            "funcionarios": funcionarios_do_caixa(loja_id) if loja_id else [],
        }
        corpo.update({"vendas_produtos": 0, "recebido": 0, "a_receber": 0})
        if aberta is None:
            return Response(corpo)
        corpo.update({
            "id": aberta.id,
            "nome": aberta.nome,
            "responsavel": aberta.responsavel_nome or aberta.operador_nome,
            "operador": aberta.responsavel_nome or aberta.operador_nome,
            "aberta_em": aberta.aberta_em.isoformat() if aberta.aberta_em else "",
            **totais_sessao_caixa(aberta),
        })
        return Response(corpo)

    def post(self, request):
        loja_id = resolve_loja_id_from_request(request)
        if not loja_id:
            return Response({"error": "Loja não identificada."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            aberta = abrir_caixa(
                loja_id,
                request.user,
                nome=request.data.get("nome") or "",
                responsavel_id=request.data.get("responsavel_id"),
            )
        except VendaProdutoError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "aberta": True,
            "id": aberta.id,
            "nome": aberta.nome,
            "responsavel": aberta.responsavel_nome,
            "operador": aberta.responsavel_nome,
            **totais_sessao_caixa(aberta),
        })


class CaixaFechamentosView(APIView):
    """Caixas fechados no dia, com o operador e o resumo da gaveta."""

    permission_classes = CLINICA_ESTOQUE

    def get(self, request):
        from datetime import datetime, time

        from django.utils import timezone
        from django.utils.dateparse import parse_date

        from .models import SessaoCaixa

        loja_id = resolve_loja_id_from_request(request)
        dia = parse_date(str(request.query_params.get("data") or "")) or timezone.localdate()
        inicio = timezone.make_aware(datetime.combine(dia, time.min))
        fim = timezone.make_aware(datetime.combine(dia, time.max))
        sessoes = (
            SessaoCaixa.objects.filter(
                loja_id=loja_id,
                status=SessaoCaixa.STATUS_FECHADA,
                fechada_em__gte=inicio,
                fechada_em__lte=fim,
            )
            .order_by("fechada_em", "id")
        )
        corpo = []
        for sessao in sessoes:
            vendas = [
                _venda_resumo(venda)
                for venda in sessao.vendas.select_related("payment", "paciente").order_by("id")
            ]
            corpo.append({
                "id": sessao.id,
                "nome": sessao.nome,
                "operador": sessao.responsavel_nome or sessao.operador_nome,
                "aberta_em": sessao.aberta_em.isoformat() if sessao.aberta_em else "",
                "fechada_em": sessao.fechada_em.isoformat() if sessao.fechada_em else "",
                **totais_gaveta(sessao),
                "vendas": vendas,
            })
        return Response(corpo)


class CaixaFecharView(APIView):
    permission_classes = CLINICA_ESTOQUE

    def post(self, request):
        loja_id = resolve_loja_id_from_request(request)
        fechar_caixa(loja_id)
        return Response({"aberta": False})


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
