from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum, Q
from datetime import date
from core.views import BaseModelViewSet
from .models import Categoria, Produto, Cliente, Pedido, ItemPedido, Cupom
from .serializers import (
    CategoriaSerializer, ProdutoSerializer, ClienteSerializer,
    PedidoSerializer, ItemPedidoSerializer, CupomSerializer
)


class CategoriaViewSet(BaseModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer


class ProdutoViewSet(BaseModelViewSet):
    queryset = Produto.objects.all()
    serializer_class = ProdutoSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        categoria_id = self.request.query_params.get('categoria_id')
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)
        return queryset


class ClienteViewSet(BaseModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset

    @action(detail=False, methods=['get'])
    def estoque_baixo(self, request):
        """Produtos com estoque baixo (menos de 10 unidades)"""
        produtos = self.queryset.filter(estoque__lt=10, is_active=True)
        serializer = self.get_serializer(produtos, many=True)
        return Response(serializer.data)


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]


class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated]

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


class ItemPedidoViewSet(viewsets.ModelViewSet):
    queryset = ItemPedido.objects.all()
    serializer_class = ItemPedidoSerializer
    permission_classes = [IsAuthenticated]


class CupomViewSet(viewsets.ModelViewSet):
    queryset = Cupom.objects.all()
    serializer_class = CupomSerializer
    permission_classes = [IsAuthenticated]

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
