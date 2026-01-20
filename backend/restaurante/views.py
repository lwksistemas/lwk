from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum
from datetime import date
from core.views import BaseModelViewSet
from .models import Categoria, ItemCardapio, Mesa, Cliente, Reserva, Pedido, ItemPedido, Funcionario
from .serializers import (
    CategoriaSerializer, ItemCardapioSerializer, MesaSerializer,
    ClienteSerializer, ReservaSerializer, PedidoSerializer,
    ItemPedidoSerializer, FuncionarioSerializer
)


class CategoriaViewSet(BaseModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer


class ItemCardapioViewSet(BaseModelViewSet):
    queryset = ItemCardapio.objects.all()
    serializer_class = ItemCardapioSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        categoria_id = self.request.query_params.get('categoria_id')
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)
        return queryset


class MesaViewSet(BaseModelViewSet):
    queryset = Mesa.objects.all()
    serializer_class = MesaSerializer


class ClienteViewSet(BaseModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer


class FuncionarioViewSet(BaseModelViewSet):
    queryset = Funcionario.objects.all()
    serializer_class = FuncionarioSerializer
        is_disponivel = self.request.query_params.get('is_disponivel')
        if is_disponivel is not None:
            queryset = queryset.filter(is_disponivel=is_disponivel.lower() == 'true')
        return queryset


class MesaViewSet(viewsets.ModelViewSet):
    queryset = Mesa.objects.all()
    serializer_class = MesaSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def disponiveis(self, request):
        """Mesas disponíveis"""
        mesas = self.queryset.filter(status='livre', is_active=True)
        serializer = self.get_serializer(mesas, many=True)
        return Response(serializer.data)


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]


class ReservaViewSet(viewsets.ModelViewSet):
    queryset = Reserva.objects.all()
    serializer_class = ReservaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        data = self.request.query_params.get('data')
        if data:
            queryset = queryset.filter(data=data)
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset

    @action(detail=False, methods=['get'])
    def hoje(self, request):
        """Reservas de hoje"""
        hoje = date.today()
        reservas = self.queryset.filter(data=hoje)
        serializer = self.get_serializer(reservas, many=True)
        return Response(serializer.data)


class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        tipo = self.request.query_params.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        return queryset

    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """Estatísticas do dashboard"""
        hoje = date.today()
        
        # Pedidos hoje
        pedidos_hoje = Pedido.objects.filter(created_at__date=hoje).count()
        
        # Mesas ocupadas
        mesas_ocupadas = Mesa.objects.filter(status='ocupada').count()
        mesas_total = Mesa.objects.filter(is_active=True).count()
        
        # Itens do cardápio
        cardapio = ItemCardapio.objects.filter(is_disponivel=True).count()
        
        # Faturamento do dia
        faturamento = Pedido.objects.filter(
            created_at__date=hoje,
            status__in=['entregue']
        ).aggregate(total=Sum('total'))['total'] or 0
        
        return Response({
            'pedidos_hoje': pedidos_hoje,
            'mesas_ocupadas': f"{mesas_ocupadas}/{mesas_total}",
            'cardapio': cardapio,
            'faturamento': float(faturamento)
        })


class ItemPedidoViewSet(viewsets.ModelViewSet):
    queryset = ItemPedido.objects.all()
    serializer_class = ItemPedidoSerializer
    permission_classes = [IsAuthenticated]


class FuncionarioViewSet(viewsets.ModelViewSet):
    queryset = Funcionario.objects.all()
    serializer_class = FuncionarioSerializer
    permission_classes = [IsAuthenticated]
