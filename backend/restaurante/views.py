from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db import models as django_models
from django.db.models import Sum
from datetime import date
from decimal import Decimal
from core.views import BaseModelViewSet, BaseFuncionarioViewSet
from tenants.middleware import get_current_loja_id
from .models import (
    Categoria, ItemCardapio, Mesa, Cliente, Reserva, Pedido, ItemPedido, Funcionario,
    Fornecedor, NotaFiscalEntrada, ItemNotaFiscalEntrada, EstoqueItem, MovimentoEstoque,
    RegistroPesoBalança
)
from .serializers import (
    CategoriaSerializer, ItemCardapioSerializer, MesaSerializer,
    ClienteSerializer, ReservaSerializer, PedidoSerializer,
    ItemPedidoSerializer, FuncionarioSerializer,
    FornecedorSerializer, NotaFiscalEntradaSerializer, EstoqueItemSerializer,
    MovimentoEstoqueSerializer, RegistroPesoBalançaSerializer
)


class CategoriaViewSet(BaseModelViewSet):
    serializer_class = CategoriaSerializer
    
    def get_queryset(self):
        """Retorna queryset filtrado por loja com prefetch_related"""
        # Otimização: prefetch_related para itens
        queryset = Categoria.objects.prefetch_related('itens')
        
        # Aplicar filtro is_active
        if hasattr(Categoria, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
        return queryset


class ItemCardapioViewSet(BaseModelViewSet):
    serializer_class = ItemCardapioSerializer

    def get_queryset(self):
        """Retorna queryset filtrado por loja e categoria"""
        # Otimização: select_related para categoria
        queryset = ItemCardapio.objects.select_related('categoria')
        
        # Aplicar filtro is_active
        if hasattr(ItemCardapio, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
        categoria_id = self.request.query_params.get('categoria_id')
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)
        return queryset


class MesaViewSet(BaseModelViewSet):
    serializer_class = MesaSerializer
    
    def get_queryset(self):
        """Retorna queryset filtrado por loja"""
        queryset = Mesa.objects.all()
        
        # Aplicar filtro is_active
        if hasattr(Mesa, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
        return queryset

    @action(detail=False, methods=['get'])
    def disponiveis(self, request):
        """Mesas disponíveis"""
        mesas = self.get_queryset().filter(status='livre')
        serializer = self.get_serializer(mesas, many=True)
        return Response(serializer.data)


class ClienteViewSet(BaseModelViewSet):
    serializer_class = ClienteSerializer
    
    def get_queryset(self):
        """Retorna queryset filtrado por loja"""
        queryset = Cliente.objects.all()
        
        # Aplicar filtro is_active
        if hasattr(Cliente, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
        return queryset


class FuncionarioViewSet(BaseFuncionarioViewSet):
    serializer_class = FuncionarioSerializer
    model_class = Funcionario
    cargo_padrao = 'gerente'


class ReservaViewSet(BaseModelViewSet):
    serializer_class = ReservaSerializer

    def get_queryset(self):
        """Retorna queryset filtrado por loja, data e status"""
        # Otimização: select_related
        queryset = Reserva.objects.select_related('cliente', 'mesa')
        
        # Aplicar filtro is_active
        if hasattr(Reserva, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
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
        reservas = self.get_queryset().filter(data=hoje)
        serializer = self.get_serializer(reservas, many=True)
        return Response(serializer.data)


class PedidoViewSet(BaseModelViewSet):
    serializer_class = PedidoSerializer

    def get_queryset(self):
        """Retorna queryset filtrado por loja, status e tipo"""
        # Otimização: select_related e prefetch_related
        queryset = Pedido.objects.select_related('cliente', 'mesa').prefetch_related('itens', 'itens__item_cardapio')
        
        # Aplicar filtro is_active
        if hasattr(Pedido, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
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


class ItemPedidoViewSet(BaseModelViewSet):
    serializer_class = ItemPedidoSerializer
    
    def get_queryset(self):
        """Retorna queryset filtrado por loja"""
        # Otimização: select_related
        queryset = ItemPedido.objects.select_related('pedido', 'item_cardapio')
        
        # Aplicar filtro is_active
        if hasattr(ItemPedido, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
        return queryset


class FornecedorViewSet(BaseModelViewSet):
    serializer_class = FornecedorSerializer
    
    def get_queryset(self):
        """Retorna queryset filtrado por loja"""
        queryset = Fornecedor.objects.all()
        
        # Aplicar filtro is_active
        if hasattr(Fornecedor, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
        return queryset


class NotaFiscalEntradaViewSet(BaseModelViewSet):
    """Entrada de NF-e: upload de XML, vinculação a fornecedor e estoque."""
    serializer_class = NotaFiscalEntradaSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_queryset(self):
        """Retorna queryset filtrado por loja e fornecedor"""
        queryset = NotaFiscalEntrada.objects.select_related('fornecedor').prefetch_related('itens')
        
        # Aplicar filtro is_active
        if hasattr(NotaFiscalEntrada, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
        fornecedor_id = self.request.query_params.get('fornecedor_id')
        if fornecedor_id:
            queryset = queryset.filter(fornecedor_id=fornecedor_id)
        return queryset


class EstoqueItemViewSet(BaseModelViewSet):
    serializer_class = EstoqueItemSerializer
    
    def get_queryset(self):
        """Retorna queryset filtrado por loja"""
        queryset = EstoqueItem.objects.all()
        
        # Aplicar filtro is_active
        if hasattr(EstoqueItem, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
        return queryset

    @action(detail=False, methods=['get'])
    def alertas(self, request):
        """Itens com estoque abaixo do mínimo."""
        queryset = self.get_queryset().filter(
            quantidade_atual__lt=django_models.F('quantidade_minima'),
            quantidade_minima__gt=0
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def movimentar(self, request, pk=None):
        """Registra entrada ou saída no estoque."""
        item = self.get_object()
        tipo = request.data.get('tipo')  # 'entrada' ou 'saida'
        quantidade = request.data.get('quantidade')
        observacao = request.data.get('observacao', '')
        if tipo not in ('entrada', 'saida'):
            return Response({'detail': 'tipo deve ser entrada ou saida'}, status=400)
        try:
            qty = Decimal(str(quantidade))
        except (TypeError, ValueError):
            return Response({'detail': 'quantidade inválida'}, status=400)
        if qty <= 0:
            return Response({'detail': 'quantidade deve ser positiva'}, status=400)
        if tipo == 'saida' and item.quantidade_atual < qty:
            return Response({'detail': 'estoque insuficiente'}, status=400)
        mov = MovimentoEstoque.objects.create(
            estoque_item=item,
            quantidade=qty,
            tipo=tipo,
            observacao=observacao or None
        )
        if tipo == 'entrada':
            item.quantidade_atual += qty
        else:
            item.quantidade_atual -= qty
        item.save(update_fields=['quantidade_atual', 'updated_at'])
        serializer = MovimentoEstoqueSerializer(mov)
        return Response(serializer.data)


class MovimentoEstoqueViewSet(viewsets.ModelViewSet):
    """Listagem e criação de movimentos de estoque (entrada/saída)."""
    serializer_class = MovimentoEstoqueSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        loja_id = get_current_loja_id()
        if not loja_id:
            return MovimentoEstoque.objects.none()
        return MovimentoEstoque.objects.filter(estoque_item__loja_id=loja_id).select_related('estoque_item')

    def perform_create(self, serializer):
        mov = serializer.save()
        item = mov.estoque_item
        if mov.tipo == MovimentoEstoque.ENTRADA:
            item.quantidade_atual += mov.quantidade
        else:
            item.quantidade_atual -= mov.quantidade
        item.save(update_fields=['quantidade_atual', 'updated_at'])


class RegistroPesoBalançaViewSet(viewsets.ModelViewSet):
    """Registro de peso (balança) por item de estoque; opção de adicionar ao estoque."""
    serializer_class = RegistroPesoBalançaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        loja_id = get_current_loja_id()
        if not loja_id:
            return RegistroPesoBalança.objects.none()
        return RegistroPesoBalança.objects.filter(estoque_item__loja_id=loja_id).select_related('estoque_item')

    def perform_create(self, serializer):
        reg = serializer.save()
        if reg.adicionar_ao_estoque and reg.peso_kg:
            item = reg.estoque_item
            MovimentoEstoque.objects.create(
                estoque_item=item,
                quantidade=reg.peso_kg,
                tipo=MovimentoEstoque.ENTRADA,
                observacao=f'Balança: {reg.peso_kg} kg' + (f' - {reg.observacao}' if reg.observacao else '')
            )
            item.quantidade_atual += reg.peso_kg
            item.save(update_fields=['quantidade_atual', 'updated_at'])
