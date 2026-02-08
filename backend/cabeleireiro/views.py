import logging
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q, Avg, F
from django.utils import timezone
from datetime import date, datetime, timedelta
from decimal import Decimal
from core.views import BaseModelViewSet, BaseFuncionarioViewSet
from core.mixins import ClienteSearchMixin
from core.throttling import DashboardRateThrottle
from .models import (
    Cliente, Profissional, Servico, Agendamento, Produto, Venda,
    Funcionario, HorarioFuncionamento, BloqueioAgenda
)
from .serializers import (
    ClienteSerializer, ProfissionalSerializer, ServicoSerializer,
    AgendamentoSerializer, ProdutoSerializer, VendaSerializer,
    FuncionarioSerializer, HorarioFuncionamentoSerializer,
    BloqueioAgendaSerializer, ClienteBuscaSerializer
)

logger = logging.getLogger(__name__)


class ClienteViewSet(ClienteSearchMixin, BaseModelViewSet):
    """ViewSet de Clientes - usa ClienteSearchMixin para busca"""
    serializer_class = ClienteSerializer
    search_serializer_class = ClienteBuscaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        """Retorna queryset filtrado por loja e is_active"""
        queryset = Cliente.objects.all()
        
        # Aplicar filtro is_active
        if hasattr(Cliente, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
        return queryset

    @action(detail=False, methods=['get'])
    def buscar(self, request):
        """Busca clientes por nome, telefone ou email"""
        return ClienteSearchMixin.buscar(self, request)


class ProfissionalViewSet(BaseModelViewSet):
    """ViewSet de Profissionais"""
    serializer_class = ProfissionalSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        """Retorna queryset filtrado por loja e is_active"""
        queryset = Profissional.objects.all()
        
        # Aplicar filtro is_active
        if hasattr(Profissional, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
        return queryset

    @action(detail=True, methods=['get'])
    def agenda(self, request, pk=None):
        """Retorna agenda do profissional"""
        profissional = self.get_object()
        data_inicio = request.query_params.get('data_inicio', date.today())
        data_fim = request.query_params.get('data_fim', date.today() + timedelta(days=7))
        
        agendamentos = Agendamento.objects.filter(
            profissional=profissional,
            data__range=[data_inicio, data_fim]
        ).order_by('data', 'horario')
        
        serializer = AgendamentoSerializer(agendamentos, many=True)
        return Response(serializer.data)


class ServicoViewSet(BaseModelViewSet):
    """ViewSet de Serviços"""
    serializer_class = ServicoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        """Retorna queryset filtrado por loja, is_active e categoria"""
        queryset = Servico.objects.all()
        
        # Aplicar filtro is_active
        if hasattr(Servico, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
        params = getattr(self.request, 'query_params', self.request.GET)
        categoria = params.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        
        return queryset


class AgendamentoViewSet(BaseModelViewSet):
    """ViewSet de Agendamentos"""
    serializer_class = AgendamentoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        """Retorna queryset filtrado por loja com select_related"""
        queryset = Agendamento.objects.select_related('cliente', 'profissional', 'servico')
        
        # Aplicar filtro is_active
        if hasattr(Agendamento, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
        params = getattr(self.request, 'query_params', self.request.GET)
        
        # Filtros
        data = params.get('data')
        if data:
            queryset = queryset.filter(data=data)
        
        status_param = params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        cliente_id = params.get('cliente_id')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        
        profissional_id = params.get('profissional_id')
        if profissional_id:
            queryset = queryset.filter(profissional_id=profissional_id)
        
        return queryset

    @action(detail=False, methods=['get'], throttle_classes=[DashboardRateThrottle])
    def dashboard(self, request):
        """
        Retorna dados para o dashboard.
        Rate limited: 10 requisições por minuto para prevenir loops infinitos.
        """
        hoje = date.today()
        inicio_mes = date(hoje.year, hoje.month, 1)
        
        empty_response = {
            'estatisticas': {
                'agendamentos_hoje': 0,
                'agendamentos_mes': 0,
                'clientes_ativos': 0,
                'servicos_ativos': 0,
                'receita_mensal': 0.0,
            },
            'proximos': [],
        }
        
        try:
            # Estatísticas
            qs = self.get_queryset()
            agendamentos_hoje = qs.filter(data=hoje).count()
            agendamentos_mes = qs.filter(data__gte=inicio_mes).count()
            clientes_ativos = Cliente.objects.filter(is_active=True).count()
            servicos_ativos = Servico.objects.filter(is_active=True).count()

            # Receita mensal
            receita_mensal = qs.filter(
                data__gte=inicio_mes,
                status='concluido'
            ).aggregate(total=Sum('valor_pago'))['total'] or Decimal('0.00')

            # Próximos agendamentos
            proximos = qs.filter(
                data__gte=hoje,
                status__in=['agendado', 'confirmado']
            ).order_by('data', 'horario')[:10]

            return Response({
                'estatisticas': {
                    'agendamentos_hoje': agendamentos_hoje,
                    'agendamentos_mes': agendamentos_mes,
                    'clientes_ativos': clientes_ativos,
                    'servicos_ativos': servicos_ativos,
                    'receita_mensal': float(receita_mensal),
                },
                'proximos': self.get_serializer(proximos, many=True).data
            })
        except Exception as e:
            logger.exception(f'[AgendamentoViewSet] Erro no dashboard: {e}')
            return Response(empty_response, status=200)

    @action(detail=False, methods=['get'])
    def calendario(self, request):
        """Retorna agendamentos para visualização em calendário"""
        data_inicio = request.query_params.get('data_inicio')
        data_fim = request.query_params.get('data_fim')
        
        if not data_inicio or not data_fim:
            return Response(
                {'error': 'data_inicio e data_fim são obrigatórios'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        agendamentos = self.get_queryset().filter(
            data__range=[data_inicio, data_fim]
        ).order_by('data', 'horario')
        
        serializer = self.get_serializer(agendamentos, many=True)
        return Response(serializer.data)


class ProdutoViewSet(BaseModelViewSet):
    """ViewSet de Produtos"""
    serializer_class = ProdutoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        """Retorna queryset filtrado por loja, is_active e categoria"""
        queryset = Produto.objects.all()
        
        # Aplicar filtro is_active
        if hasattr(Produto, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
        params = getattr(self.request, 'query_params', self.request.GET)
        
        categoria = params.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        
        estoque_baixo = params.get('estoque_baixo')
        if estoque_baixo == 'true':
            queryset = queryset.filter(estoque_atual__lte=F('estoque_minimo'))
        
        return queryset

    @action(detail=False, methods=['get'])
    def estoque_baixo(self, request):
        """Retorna produtos com estoque baixo"""
        produtos = self.get_queryset().filter(
            estoque_atual__lte=F('estoque_minimo')
        )
        serializer = self.get_serializer(produtos, many=True)
        return Response(serializer.data)


class VendaViewSet(BaseModelViewSet):
    """ViewSet de Vendas"""
    serializer_class = VendaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        """Retorna queryset filtrado por loja com select_related"""
        queryset = Venda.objects.select_related('cliente', 'produto')
        
        # Aplicar filtro is_active
        if hasattr(Venda, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
        return queryset

    def perform_create(self, serializer):
        """Ao criar venda, atualiza estoque do produto"""
        venda = serializer.save()
        produto = venda.produto
        produto.estoque_atual -= venda.quantidade
        produto.save()

    @action(detail=False, methods=['get'])
    def relatorio(self, request):
        """Retorna relatório de vendas"""
        data_inicio = request.query_params.get('data_inicio')
        data_fim = request.query_params.get('data_fim')
        
        queryset = self.get_queryset()
        if data_inicio:
            queryset = queryset.filter(data_venda__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(data_venda__lte=data_fim)
        
        total_vendas = queryset.aggregate(
            total=Sum('valor_total'),
            quantidade=Count('id')
        )
        
        vendas_por_forma = queryset.values('forma_pagamento').annotate(
            total=Sum('valor_total'),
            quantidade=Count('id')
        )
        
        return Response({
            'total_vendas': total_vendas,
            'vendas_por_forma_pagamento': vendas_por_forma,
            'vendas': self.get_serializer(queryset, many=True).data
        })


class FuncionarioViewSet(BaseFuncionarioViewSet):
    """ViewSet de Funcionários - usa BaseFuncionarioViewSet"""
    serializer_class = FuncionarioSerializer
    permission_classes = [IsAuthenticated]
    model_class = Funcionario
    pagination_class = None
    cargo_padrao = 'Administrador'


class HorarioFuncionamentoViewSet(BaseModelViewSet):
    """ViewSet de Horários de Funcionamento"""
    serializer_class = HorarioFuncionamentoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        """Retorna queryset filtrado por loja e is_active"""
        queryset = HorarioFuncionamento.objects.all()
        
        # Aplicar filtro is_active
        if hasattr(HorarioFuncionamento, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
        return queryset


class BloqueioAgendaViewSet(BaseModelViewSet):
    """ViewSet de Bloqueios de Agenda"""
    serializer_class = BloqueioAgendaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        """Retorna queryset filtrado por loja e profissional"""
        queryset = BloqueioAgenda.objects.select_related('profissional')
        
        # Aplicar filtro is_active
        if hasattr(BloqueioAgenda, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
        params = getattr(self.request, 'query_params', self.request.GET)
        profissional_id = params.get('profissional_id')
        if profissional_id:
            queryset = queryset.filter(profissional_id=profissional_id)
        
        return queryset
