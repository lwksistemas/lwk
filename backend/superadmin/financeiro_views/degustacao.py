"""Escolha do cliente quando a demonstração acaba: pagar ou cancelar."""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from superadmin.degustacao_service import aceitar_boleto_degustacao, cancelar_degustacao
from superadmin.models import FinanceiroLoja


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def decidir_degustacao_loja(request, loja_slug):
    """Gera o boleto só na escolha de pagar. Cancelar encerra sem cobrança."""
    from .dashboard_loja import _resolver_loja_por_permissao

    loja, err = _resolver_loja_por_permissao(request, loja_slug)
    if err:
        return err

    try:
        financeiro = loja.financeiro
    except FinanceiroLoja.DoesNotExist:
        return Response(
            {"success": False, "error": "Financeiro da loja não encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )

    acao = str(request.data.get("acao") or "").strip().lower()
    if acao == "pagar":
        resultado = aceitar_boleto_degustacao(loja, financeiro)
    elif acao == "cancelar":
        resultado = cancelar_degustacao(loja, financeiro)
    else:
        return Response(
            {"success": False, "error": "Escolha pagar ou cancelar."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    codigo = status.HTTP_200_OK if resultado.get("success") else status.HTTP_400_BAD_REQUEST
    return Response(resultado, status=codigo)
