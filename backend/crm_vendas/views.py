from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import date
from core.views import BaseModelViewSet
from .models import Lead, Cliente, Vendedor, Produto, Venda, Pipeline
from .serializers import (
    LeadSerializer, ClienteSerializer, VendedorSerializer,
    ProdutoSerializer, VendaSerializer, PipelineSerializer
)


class LeadViewSet(BaseModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrar por status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filtrar por origem
        origem = self.request.query_params.get('origem')
        if origem:
            queryset = queryset.filter(origem=origem)
        
        return queryset


class ClienteViewSet(BaseModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer


class VendedorViewSet(BaseModelViewSet):
    queryset = Vendedor.objects.all()
    serializer_class = VendedorSerializer


class ProdutoViewSet(BaseModelViewSet):
    queryset = Produto.objects.all()
    serializer_class = ProdutoSerializer
            queryset = queryset.filter(origem=origem)
        
        return queryset

    @action(detail=False, methods=['get'])
    def recentes(self, request):
        """Retorna leads mais recentes"""
        leads = self.queryset.order_by('-created_at')[:10]
        serializer = self.get_serializer(leads, many=True)
        return Response(serializer.data)


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset


class VendedorViewSet(viewsets.ModelViewSet):
    queryset = Vendedor.objects.all()
    serializer_class = VendedorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset


class ProdutoViewSet(viewsets.ModelViewSet):
    queryset = Produto.objects.all()
    serializer_class = ProdutoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        categoria = self.request.query_params.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        return queryset


class VendaViewSet(viewsets.ModelViewSet):
    queryset = Venda.objects.all()
    serializer_class = VendaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        
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


class PipelineViewSet(viewsets.ModelViewSet):
    queryset = Pipeline.objects.all()
    serializer_class = PipelineSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset
