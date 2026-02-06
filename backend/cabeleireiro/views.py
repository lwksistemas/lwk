import logging
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q, Avg
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


class ClienteViewSet(ClienteSearchMixin, BaseModelViewSet):
    """ViewSet de Clientes - usa ClienteSearchMixin para busca"""
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    search_serializer_class = ClienteBuscaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # ✅ Desabilitar paginação para retornar todos os clientes

    @action(detail=False, methods=['get'])
    def buscar(self, request):
        """Busca clientes por nome, telefone ou email"""
        return ClienteSearchMixin.buscar(self, request)


class ProfissionalViewSet(BaseModelViewSet):
    """ViewSet de Profissionais"""
    queryset = Profissional.objects.all()
    serializer_class = ProfissionalSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # ✅ Desabilitar paginação

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
    queryset = Servico.objects.all()
    serializer_class = ServicoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # ✅ Desabilitar paginação

    def get_queryset(self):
        queryset = super().get_queryset()
        params = getattr(self.request, 'query_params', self.request.GET)
        
        categoria = params.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        
        return queryset


class AgendamentoViewSet(BaseModelViewSet):
    """ViewSet de Agendamentos"""
    queryset = Agendamento.objects.select_related('cliente', 'profissional', 'servico')
    pagination_class = None  # ✅ Desabilitar paginação
    serializer_class = AgendamentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
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
        Em caso de erro (ex.: tabelas não existem no schema da loja), retorna dados vazios para não quebrar a página.
        """
        logger = logging.getLogger(__name__)
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
            'aviso': 'Dados do dashboard não disponíveis no momento. Verifique se as tabelas da loja foram criadas.',
        }
        try:
            # Estatísticas
            agendamentos_hoje = self.get_queryset().filter(data=hoje).count()
            agendamentos_mes = self.get_queryset().filter(data__gte=inicio_mes).count()
            clientes_ativos = Cliente.objects.filter(is_active=True).count()
            servicos_ativos = Servico.objects.filter(is_active=True).count()

            # Receita mensal
            receita_mensal = self.get_queryset().filter(
                data__gte=inicio_mes,
                status='concluido'
            ).aggregate(total=Sum('valor_pago'))['total'] or Decimal('0.00')

            # Próximos agendamentos
            proximos = self.get_queryset().filter(
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
                'proximos': AgendamentoSerializer(proximos, many=True).data
            })
        except Exception as e:
            logger.exception(
                'cabeleireiro dashboard erro (loja pode não ter schema/tabelas): %s',
                e,
                extra={'request_path': getattr(request, 'path', None)},
            )
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

    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """Retorna estatísticas gerais"""
        hoje = date.today()
        inicio_mes = date(hoje.year, hoje.month, 1)
        
        agendamentos_hoje = self.get_queryset().filter(data=hoje).count()
        agendamentos_mes = self.get_queryset().filter(data__gte=inicio_mes).count()
        clientes_ativos = Cliente.objects.filter(is_active=True).count()
        servicos_ativos = Servico.objects.filter(is_active=True).count()
        
        receita_mensal = self.get_queryset().filter(
            data__gte=inicio_mes,
            status='concluido'
        ).aggregate(total=Sum('valor_pago'))['total'] or Decimal('0.00')
        
        return Response({
            'agendamentos_hoje': agendamentos_hoje,
            'agendamentos_mes': agendamentos_mes,
            'clientes_ativos': clientes_ativos,
            'servicos_ativos': servicos_ativos,
            'receita_mensal': float(receita_mensal),
        })


class ProdutoViewSet(BaseModelViewSet):
    """ViewSet de Produtos"""
    queryset = Produto.objects.all()
    serializer_class = ProdutoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # ✅ Desabilitar paginação

    def get_queryset(self):
        queryset = super().get_queryset()
        params = getattr(self.request, 'query_params', self.request.GET)
        
        categoria = params.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        
        estoque_baixo = params.get('estoque_baixo')
        if estoque_baixo == 'true':
            queryset = queryset.filter(estoque_atual__lte=models.F('estoque_minimo'))
        
        return queryset

    @action(detail=False, methods=['get'])
    def estoque_baixo(self, request):
        """Retorna produtos com estoque baixo"""
        from django.db.models import F
        produtos = self.get_queryset().filter(
            estoque_atual__lte=F('estoque_minimo'),
            is_active=True
        )
        serializer = self.get_serializer(produtos, many=True)
        return Response(serializer.data)


class VendaViewSet(BaseModelViewSet):
    """ViewSet de Vendas"""
    queryset = Venda.objects.select_related('cliente', 'produto')
    serializer_class = VendaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # ✅ Desabilitar paginação

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
    queryset = Funcionario.objects.all()
    serializer_class = FuncionarioSerializer
    permission_classes = [IsAuthenticated]
    model_class = Funcionario  # ✅ Necessário para BaseFuncionarioViewSet
    pagination_class = None  # ✅ Desabilitar paginação
    cargo_padrao = 'Administrador'


class HorarioFuncionamentoViewSet(BaseModelViewSet):
    """ViewSet de Horários de Funcionamento"""
    queryset = HorarioFuncionamento.objects.all()
    serializer_class = HorarioFuncionamentoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # ✅ Desabilitar paginação


class BloqueioAgendaViewSet(BaseModelViewSet):
    """ViewSet de Bloqueios de Agenda"""
    queryset = BloqueioAgenda.objects.select_related('profissional')
    serializer_class = BloqueioAgendaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # ✅ Desabilitar paginação

    def get_queryset(self):
        queryset = super().get_queryset()
        params = getattr(self.request, 'query_params', self.request.GET)
        
        profissional_id = params.get('profissional_id')
        if profissional_id:
            queryset = queryset.filter(profissional_id=profissional_id)
        
        return queryset
