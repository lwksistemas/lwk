"""Renovação / geração de cobrança das lojas."""
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..loja_utils import resolve_loja_by_slug_or_atalho
from ..models import FinanceiroLoja
from .helpers import _get_or_create_financeiro_loja

logger = logging.getLogger(__name__)

def _executar_renovar_financeiro(financeiro, data):
    """Lógica compartilhada para gerar cobrança (antecipada ou renovação)."""
    from superadmin.cobranca_service import CobrancaService

    loja = financeiro.loja
    dia_vencimento = data.get('dia_vencimento')
    antecipado = bool(data.get('antecipado', False))

    if dia_vencimento is not None and not antecipado:
        try:
            dia_vencimento = int(dia_vencimento)
            if dia_vencimento < 1 or dia_vencimento > 28:
                return Response(
                    {'success': False, 'error': 'dia_vencimento deve estar entre 1 e 28'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except (ValueError, TypeError):
            return Response(
                {'success': False, 'error': 'dia_vencimento deve ser um número inteiro'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    try:
        logger.info(
            'Renovando assinatura loja %s (financeiro_id=%s, antecipado=%s)',
            loja.slug, financeiro.id, antecipado,
        )
        result = CobrancaService().renovar_cobranca(loja, financeiro, dia_vencimento, antecipado=antecipado)
        if result.get('success'):
            return Response(result, status=status.HTTP_200_OK)
        return Response(
            {'success': False, 'error': result.get('error', 'Erro ao gerar cobrança')},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.exception('Erro ao renovar assinatura loja %s: %s', loja.slug, e)
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def renovar_assinatura_loja(request, loja_slug):
    """Gera boleto/PIX para o proprietário pagar (slug ou atalho na URL)."""
    if not request.user.is_superuser:
        loja = resolve_loja_by_slug_or_atalho(loja_slug, owner=request.user, is_active=True)
        if not loja:
            return Response(
                {'success': False, 'error': 'Sem permissão. Apenas o responsável pode gerar cobrança.'},
                status=status.HTTP_403_FORBIDDEN,
            )
    else:
        loja = resolve_loja_by_slug_or_atalho(loja_slug, is_active=True)
        if not loja:
            return Response({'success': False, 'error': 'Loja não encontrada'}, status=status.HTTP_404_NOT_FOUND)

    try:
        financeiro = _get_or_create_financeiro_loja(loja)
    except Exception as e:
        logger.exception('renovar_assinatura_loja financeiro %s: %s', loja_slug, e)
        return Response(
            {'success': False, 'error': 'Não foi possível carregar o financeiro da loja.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return _executar_renovar_financeiro(financeiro, request.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def renovar_financeiro_por_id(request, financeiro_id):
    """Gera boleto/PIX pelo ID do FinanceiroLoja (compatível com loja-financeiro/{id}/renovar/)."""
    qs = FinanceiroLoja.objects.select_related('loja', 'loja__plano')
    if not request.user.is_superuser:
        financeiro = qs.filter(id=financeiro_id, loja__owner=request.user, loja__is_active=True).first()
        if not financeiro:
            return Response(
                {'success': False, 'error': 'Sem permissão ou financeiro não encontrado.'},
                status=status.HTTP_403_FORBIDDEN,
            )
    else:
        financeiro = qs.filter(id=financeiro_id).first()
        if not financeiro:
            return Response({'success': False, 'error': 'Financeiro não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    return _executar_renovar_financeiro(financeiro, request.data)
