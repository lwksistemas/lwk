from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from datetime import date
from core.views import BaseModelViewSet
from .models import Categoria, Produto, Cliente, Pedido, ItemPedido, Cupom
from .serializers import (
    CategoriaSerializer, ProdutoSerializer, ClienteSerializer,
    PedidoSerializer, ItemPedidoSerializer, CupomSerializer
)


class CategoriaViewSet(BaseModelViewSet):
    # Otimização: prefetch_related para produtos
    queryset = Categoria.objects.prefetch_related('produtos').all()
    serializer_class = CategoriaSerializer


class ProdutoViewSet(BaseModelViewSet):
    # Otimização: select_related para categoria
    queryset = Produto.objects.select_related('categoria').all()
    serializer_class = ProdutoSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        categoria_id = self.request.query_params.get('categoria_id')
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset

    @action(detail=False, methods=['get'])
    def estoque_baixo(self, request):
        """Produtos com estoque baixo (menos de 10 unidades)"""
        produtos = self.queryset.filter(estoque__lt=10, is_active=True)
        serializer = self.get_serializer(produtos, many=True)
        return Response(serializer.data)


class ClienteViewSet(BaseModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset


class PedidoViewSet(BaseModelViewSet):
    # Otimização: select_related e prefetch_related
    queryset = Pedido.objects.select_related('cliente').prefetch_related('itens', 'itens__produto').all()
    serializer_class = PedidoSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset

    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """Estatísticas do dashboard"""
        hoje = date.today()
        primeiro_dia_mes = hoje.replace(day=1)
        
        # Pedidos hoje
        pedidos_hoje = Pedido.objects.filter(created_at__date=hoje).count()
        
        # Total de produtos
        produtos = Produto.objects.filter(is_active=True).count()
        
        # Estoque total
        estoque = Produto.objects.filter(is_active=True).aggregate(total=Sum('estoque'))['total'] or 0
        
        # Faturamento do mês
        faturamento = Pedido.objects.filter(
            created_at__date__gte=primeiro_dia_mes,
            created_at__date__lte=hoje,
            status__in=['pago', 'enviado', 'entregue']
        ).aggregate(total=Sum('total'))['total'] or 0
        
        return Response({
            'pedidos_hoje': pedidos_hoje,
            'produtos': produtos,
            'estoque': estoque,
            'faturamento': float(faturamento)
        })


class ItemPedidoViewSet(BaseModelViewSet):
    # Otimização: select_related
    queryset = ItemPedido.objects.select_related('pedido', 'produto').all()
    serializer_class = ItemPedidoSerializer


class CupomViewSet(BaseModelViewSet):
    queryset = Cupom.objects.all()
    serializer_class = CupomSerializer

    @action(detail=False, methods=['post'])
    def validar(self, request):
        """Valida um cupom"""
        codigo = request.data.get('codigo')
        valor_pedido = float(request.data.get('valor_pedido', 0))
        
        try:
            cupom = Cupom.objects.get(codigo=codigo, is_active=True)
            hoje = date.today()
            
            if cupom.data_inicio > hoje or cupom.data_fim < hoje:
                return Response({'erro': 'Cupom expirado'}, status=400)
            
            if cupom.quantidade_disponivel <= 0:
                return Response({'erro': 'Cupom esgotado'}, status=400)
            
            if valor_pedido < cupom.valor_minimo:
                return Response({'erro': f'Valor mínimo: R$ {cupom.valor_minimo}'}, status=400)
            
            # Calcular desconto
            if cupom.tipo == 'percentual':
                desconto = (valor_pedido * cupom.valor) / 100
            else:
                desconto = cupom.valor
            
            return Response({
                'valido': True,
                'desconto': float(desconto),
                'tipo': cupom.tipo
            })
        except Cupom.DoesNotExist:
            return Response({'erro': 'Cupom inválido'}, status=404)
