from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db import models as django_models
from django.db.models import Sum
from datetime import date
from decimal import Decimal
from core.views import BaseModelViewSet
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
    # Otimização: prefetch_related para itens
    queryset = Categoria.objects.prefetch_related('itens').all()
    serializer_class = CategoriaSerializer


class ItemCardapioViewSet(BaseModelViewSet):
    # Otimização: select_related para categoria
    queryset = ItemCardapio.objects.select_related('categoria').all()
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

    @action(detail=False, methods=['get'])
    def disponiveis(self, request):
        """Mesas disponíveis"""
        mesas = self.queryset.filter(status='livre', is_active=True)
        serializer = self.get_serializer(mesas, many=True)
        return Response(serializer.data)


class ClienteViewSet(BaseModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer


class FuncionarioViewSet(BaseModelViewSet):
    serializer_class = FuncionarioSerializer
    
    def _ensure_owner_funcionario(self):
        """Garante que o administrador da loja exista como funcionário."""
        from core.utils import ensure_owner_as_funcionario
        ensure_owner_as_funcionario(Funcionario, cargo_padrao='gerente')
        except Loja.DoesNotExist:
            logger.error(f"❌ [_ensure_owner_funcionario] Loja {loja_id} não encontrada")
        except Exception as e:
            logger.error(f"❌ [_ensure_owner_funcionario] Erro ao criar funcionário admin: {e}")

    def list(self, request, *args, **kwargs):
        """
        Lista funcionários garantindo que o admin existe e o queryset é avaliado
        ANTES do contexto ser limpo pelo middleware
        """
        import logging
        from tenants.middleware import get_current_loja_id
        logger = logging.getLogger(__name__)
        
        loja_id_inicio = get_current_loja_id()
        logger.info(f"🔍 [FuncionarioViewSet.list RESTAURANTE] INÍCIO - loja_id={loja_id_inicio}")
        
        # 1. Garantir que admin existe
        self._ensure_owner_funcionario()
        
        loja_id_apos_ensure = get_current_loja_id()
        logger.info(f"🔍 [FuncionarioViewSet.list RESTAURANTE] Após _ensure_owner - loja_id={loja_id_apos_ensure}")
        
        # 2. Obter queryset (ainda lazy)
        queryset = self.filter_queryset(self.get_queryset())
        
        loja_id_apos_queryset = get_current_loja_id()
        logger.info(f"🔍 [FuncionarioViewSet.list RESTAURANTE] Após get_queryset - loja_id={loja_id_apos_queryset}")
        
        # 3. FORÇAR avaliação do queryset AGORA (antes do middleware limpar contexto)
        # Isso converte o queryset lazy em uma lista concreta
        funcionarios_list = list(queryset)
        
        loja_id_apos_list = get_current_loja_id()
        logger.info(f"✅ [FuncionarioViewSet.list RESTAURANTE] Queryset avaliado - {len(funcionarios_list)} funcionários encontrados - loja_id={loja_id_apos_list}")
        
        # 4. Serializar a lista concreta
        page = self.paginate_queryset(funcionarios_list)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(funcionarios_list, many=True)
        return Response(serializer.data)
    
    def get_queryset(self):
        """
        Retorna queryset filtrado por loja
        IMPORTANTE: Obter queryset dinamicamente (não usar atributo de classe)
        """
        import logging
        from tenants.middleware import get_current_loja_id
        logger = logging.getLogger(__name__)
        
        loja_id = get_current_loja_id()
        logger.info(f"🔍 [FuncionarioViewSet.get_queryset RESTAURANTE] loja_id no contexto: {loja_id}")
        
        if not loja_id:
            logger.critical("🚨 [FuncionarioViewSet RESTAURANTE] Tentativa de acesso sem loja_id no contexto")
            return Funcionario.objects.none()
        
        # IMPORTANTE: Garantir que admin existe antes de filtrar
        self._ensure_owner_funcionario()
        
        # Obter queryset dinamicamente (não usar self.queryset)
        queryset = Funcionario.objects.filter(is_active=True)
        logger.info(f"📊 [FuncionarioViewSet.get_queryset RESTAURANTE] Queryset obtido dinamicamente")
        
        return queryset


class ReservaViewSet(BaseModelViewSet):
    # Otimização: select_related
    queryset = Reserva.objects.select_related('cliente', 'mesa').all()
    serializer_class = ReservaSerializer

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


class PedidoViewSet(BaseModelViewSet):
    # Otimização: select_related e prefetch_related
    queryset = Pedido.objects.select_related('cliente', 'mesa').prefetch_related('itens', 'itens__item_cardapio').all()
    serializer_class = PedidoSerializer

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


class ItemPedidoViewSet(BaseModelViewSet):
    # Otimização: select_related
    queryset = ItemPedido.objects.select_related('pedido', 'item_cardapio').all()
    serializer_class = ItemPedidoSerializer


class FornecedorViewSet(BaseModelViewSet):
    queryset = Fornecedor.objects.all()
    serializer_class = FornecedorSerializer


class NotaFiscalEntradaViewSet(BaseModelViewSet):
    """Entrada de NF-e: upload de XML, vinculação a fornecedor e estoque."""
    queryset = NotaFiscalEntrada.objects.select_related('fornecedor').prefetch_related('itens').all()
    serializer_class = NotaFiscalEntradaSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_queryset(self):
        queryset = super().get_queryset()
        fornecedor_id = self.request.query_params.get('fornecedor_id')
        if fornecedor_id:
            queryset = queryset.filter(fornecedor_id=fornecedor_id)
        return queryset


class EstoqueItemViewSet(BaseModelViewSet):
    queryset = EstoqueItem.objects.all()
    serializer_class = EstoqueItemSerializer

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
