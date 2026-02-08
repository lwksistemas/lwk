from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from datetime import date
from core.views import BaseModelViewSet, BaseFuncionarioViewSet
from .models import Lead, Cliente, Vendedor, Produto, Venda, Pipeline
from .serializers import (
    LeadSerializer, ClienteSerializer, VendedorSerializer,
    ProdutoSerializer, VendaSerializer, PipelineSerializer
)


class LeadViewSet(BaseModelViewSet):
    serializer_class = LeadSerializer

    def get_queryset(self):
        """Retorna queryset filtrado por loja e is_active"""
        queryset = Lead.objects.all()
        
        # Aplicar filtro is_active
        if hasattr(Lead, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
        # Filtrar por status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filtrar por origem
        origem = self.request.query_params.get('origem')
        if origem:
            queryset = queryset.filter(origem=origem)
        
        return queryset

    @action(detail=False, methods=['get'])
    def recentes(self, request):
        """Retorna leads mais recentes (respeitando loja do contexto)"""
        queryset = self.get_queryset().order_by('-created_at')[:10]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ClienteViewSet(BaseModelViewSet):
    serializer_class = ClienteSerializer

    def get_queryset(self):
        """Retorna queryset filtrado por loja e is_active"""
        queryset = Cliente.objects.all()
        
        # Aplicar filtro is_active (padrão: apenas ativos)
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        elif hasattr(Cliente, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
        return queryset


class VendedorViewSet(BaseFuncionarioViewSet):
    serializer_class = VendedorSerializer
    model_class = Vendedor
    cargo_padrao = 'Administrador'


class ProdutoViewSet(BaseModelViewSet):
    serializer_class = ProdutoSerializer

    def get_queryset(self):
        """Retorna queryset filtrado por loja e is_active"""
        queryset = Produto.objects.all()
        
        # Aplicar filtro is_active (padrão: apenas ativos)
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        elif hasattr(Produto, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
        # Filtrar por categoria
        categoria = self.request.query_params.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        
        return queryset


class VendaViewSet(BaseModelViewSet):
    serializer_class = VendaSerializer

    def get_queryset(self):
        """Retorna queryset filtrado por loja com select_related"""
        # Otimização: select_related para evitar N+1
        queryset = Venda.objects.select_related('cliente', 'vendedor', 'produto')
        
        # Aplicar filtro is_active
        if hasattr(Venda, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
        # Filtrar por status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filtrar por cliente
        cliente_id = self.request.query_params.get('cliente_id')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        
        # Filtrar por vendedor
        vendedor_id = self.request.query_params.get('vendedor_id')
        if vendedor_id:
            queryset = queryset.filter(vendedor_id=vendedor_id)
        
        return queryset

    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """Retorna estatísticas do dashboard"""
        hoje = date.today()
        primeiro_dia_mes = hoje.replace(day=1)
        
        # Leads ativos (não perdidos)
        leads_ativos = Lead.objects.exclude(status='perdido').count()
        
        # Negociações (vendas em negociação)
        negociacoes = Venda.objects.filter(status='em_negociacao').count()
        
        # Vendas do mês
        vendas_mes = Venda.objects.filter(
            data_fechamento__gte=primeiro_dia_mes,
            data_fechamento__lte=hoje,
            status='fechada'
        ).count()
        
        # Receita do mês
        receita = Venda.objects.filter(
            data_fechamento__gte=primeiro_dia_mes,
            data_fechamento__lte=hoje,
            status='fechada'
        ).aggregate(total=Sum('valor'))['total'] or 0
        
        return Response({
            'leads_ativos': leads_ativos,
            'negociacoes': negociacoes,
            'vendas_mes': vendas_mes,
            'receita': float(receita)
        })


class PipelineViewSet(BaseModelViewSet):
    serializer_class = PipelineSerializer

    def get_queryset(self):
        """Retorna queryset filtrado por loja e is_active"""
        queryset = Pipeline.objects.all()
        
        # Aplicar filtro is_active (padrão: apenas ativos)
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        elif hasattr(Pipeline, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
        return queryset
