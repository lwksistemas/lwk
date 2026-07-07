from datetime import timedelta
from decimal import Decimal

from django.core.cache import cache
from django.db.models import Sum, Q, Count
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.views import BaseModelViewSet
from tenants.middleware import get_current_loja_id
from .models import CategoriaFinanceira, Transacao
from .serializers import (
    CategoriaFinanceiraSerializer, TransacaoSerializer, TransacaoResumoSerializer,
)


class CategoriaFinanceiraViewSet(BaseModelViewSet):
    """
    ViewSet para Categorias Financeiras
    CRUD completo com filtros
    """
    serializer_class = CategoriaFinanceiraSerializer
    permission_classes = [IsAuthenticated]
    
    queryset = CategoriaFinanceira.objects.all()

    def get_queryset(self):
        qs = super().get_queryset().order_by('tipo', 'nome')
        params = self.request.query_params
        
        tipo = params.get('tipo')
        if tipo:
            qs = qs.filter(tipo=tipo)
        is_active = params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')
        return qs


class TransacaoViewSet(BaseModelViewSet):
    """
    ViewSet para Transações Financeiras
    Com ações customizadas e relatórios
    """
    serializer_class = TransacaoSerializer
    permission_classes = [IsAuthenticated]
    
    queryset = Transacao.objects.select_related('categoria', 'cliente').all()

    def get_queryset(self):
        qs = super().get_queryset().order_by('-data_vencimento')
        params = self.request.query_params

        tipo = params.get('tipo')
        if tipo:
            qs = qs.filter(tipo=tipo)
        status_param = params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)
        categoria_id = params.get('categoria')
        if categoria_id:
            qs = qs.filter(categoria_id=categoria_id)
        data_inicio = params.get('data_inicio')
        data_fim = params.get('data_fim')
        if data_inicio:
            qs = qs.filter(data_vencimento__gte=data_inicio)
        if data_fim:
            qs = qs.filter(data_vencimento__lte=data_fim)
        return qs
    
    def perform_create(self, serializer):
        """
        Adiciona created_by automaticamente
        """
        user = self.request.user
        created_by = user.get_full_name() or user.username
        serializer.save(created_by=created_by)
    
    @action(detail=True, methods=['post'])
    def marcar_como_pago(self, request, pk=None):
        """
        Marca transação como paga
        """
        transacao = self.get_object()
        
        forma_pagamento = request.data.get('forma_pagamento')
        data_pagamento = request.data.get('data_pagamento')
        valor_pago = request.data.get('valor_pago', transacao.valor)
        
        if not forma_pagamento:
            return Response(
                {'error': 'Forma de pagamento é obrigatória'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        transacao.status = 'pago'
        transacao.forma_pagamento = forma_pagamento
        transacao.valor_pago = valor_pago
        
        if data_pagamento:
            transacao.data_pagamento = data_pagamento
        else:
            transacao.data_pagamento = timezone.now().date()
        
        transacao.save()
        
        serializer = self.get_serializer(transacao)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """
        Cancela transação
        """
        transacao = self.get_object()
        
        if transacao.status == 'pago':
            return Response(
                {'error': 'Não é possível cancelar uma transação já paga'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        transacao.status = 'cancelado'
        transacao.save()
        
        serializer = self.get_serializer(transacao)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def resumo(self, request):
        """Retorna resumo financeiro do período. Cached por 120s."""
        params = request.query_params
        data_inicio = params.get('data_inicio')
        data_fim = params.get('data_fim')

        if not data_inicio or not data_fim:
            hoje = timezone.now().date()
            data_inicio = hoje.replace(day=1)
            if hoje.month == 12:
                data_fim = hoje.replace(year=hoje.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                data_fim = hoje.replace(month=hoje.month + 1, day=1) - timedelta(days=1)

        loja_id = get_current_loja_id()
        cache_key = f'clinica:fin_resumo:{loja_id}:{data_inicio}:{data_fim}'
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        transacoes = Transacao.objects.filter(
            data_vencimento__gte=data_inicio,
            data_vencimento__lte=data_fim,
        )

        receitas = transacoes.filter(tipo='receita')
        total_receitas = receitas.aggregate(total=Sum('valor'))['total'] or Decimal('0')
        receitas_pagas = receitas.filter(status='pago').aggregate(total=Sum('valor_pago'))['total'] or Decimal('0')
        receitas_pendentes = receitas.filter(status='pendente').aggregate(total=Sum('valor'))['total'] or Decimal('0')

        despesas = transacoes.filter(tipo='despesa')
        total_despesas = despesas.aggregate(total=Sum('valor'))['total'] or Decimal('0')
        despesas_pagas = despesas.filter(status='pago').aggregate(total=Sum('valor_pago'))['total'] or Decimal('0')
        despesas_pendentes = despesas.filter(status='pendente').aggregate(total=Sum('valor'))['total'] or Decimal('0')

        saldo = receitas_pagas - despesas_pagas

        hoje = timezone.now().date()
        atrasados = transacoes.filter(status='pendente', data_vencimento__lt=hoje)
        transacoes_atrasadas = atrasados.count()
        valor_atrasado = atrasados.aggregate(total=Sum('valor'))['total'] or Decimal('0')

        resumo_data = {
            'total_receitas': float(total_receitas),
            'total_despesas': float(total_despesas),
            'saldo': float(saldo),
            'receitas_pendentes': float(receitas_pendentes),
            'despesas_pendentes': float(despesas_pendentes),
            'receitas_pagas': float(receitas_pagas),
            'despesas_pagas': float(despesas_pagas),
            'transacoes_atrasadas': transacoes_atrasadas,
            'valor_atrasado': float(valor_atrasado),
        }

        serializer = TransacaoResumoSerializer(resumo_data)
        cache.set(cache_key, serializer.data, 120)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def fluxo_caixa(self, request):
        """Retorna fluxo de caixa diário do período."""
        params = request.query_params

        data_fim = timezone.now().date()
        data_inicio = data_fim - timedelta(days=30)

        if params.get('data_inicio'):
            data_inicio = params.get('data_inicio')
        if params.get('data_fim'):
            data_fim = params.get('data_fim')

        transacoes = Transacao.objects.filter(
            data_vencimento__gte=data_inicio,
            data_vencimento__lte=data_fim,
            status='pago',
        ).values('data_pagamento').annotate(
            receitas=Sum('valor_pago', filter=Q(tipo='receita')),
            despesas=Sum('valor_pago', filter=Q(tipo='despesa')),
        ).order_by('data_pagamento')

        fluxo = []
        for item in transacoes:
            rec = float(item['receitas'] or Decimal('0'))
            desp = float(item['despesas'] or Decimal('0'))
            fluxo.append({
                'data': item['data_pagamento'],
                'receitas': rec,
                'despesas': desp,
                'saldo': rec - desp,
            })

        return Response(fluxo)
