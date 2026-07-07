import logging

from django.core.cache import cache
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import date, datetime, timedelta
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.views import BaseModelViewSet
from core.throttling import DashboardRateThrottle
from tenants.middleware import get_current_loja_id, get_current_tenant_db
from .models import (
    Cliente, Profissional, Procedimento, Agendamento,
    BloqueioAgenda, Consulta, HorarioTrabalhoProfissional,
)
from .serializers import (
    AgendamentoSerializer, BloqueioAgendaSerializer, ConsultaSerializer,
)

logger = logging.getLogger(__name__)


class AgendamentoViewSet(BaseModelViewSet):
    queryset = Agendamento.objects.select_related('cliente', 'profissional', 'procedimento').all()
    serializer_class = AgendamentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params

        data = params.get('data')
        if data:
            qs = qs.filter(data=data)
        status_param = params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)
        cliente_id = params.get('cliente_id')
        if cliente_id:
            qs = qs.filter(cliente_id=cliente_id)
        profissional_id = params.get('profissional_id')
        if profissional_id:
            qs = qs.filter(profissional_id=profissional_id)
        return qs

    @action(detail=False, methods=['get'])
    def calendario(self, request):
        """Retorna agendamentos para visualização em calendário."""
        params = request.query_params
        data_inicio = params.get('data_inicio')
        data_fim = params.get('data_fim')
        
        if not data_inicio or not data_fim:
            return Response({'error': 'data_inicio e data_fim são obrigatórios'}, 
                          status=status.HTTP_400_BAD_REQUEST)

        # Usar get_queryset() para respeitar filtros (ex.: profissional_id) e isolamento por loja
        qs = self.get_queryset()
        agendamentos = qs.filter(
            data__gte=data_inicio,
            data__lte=data_fim
        ).order_by('data', 'horario')
        
        serializer = self.get_serializer(agendamentos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def proximos(self, request):
        """Retorna próximos agendamentos"""
        hoje = date.today()
        agendamentos = self.get_queryset().filter(
            data__gte=hoje,
            status__in=['agendado', 'confirmado']
        ).order_by('data', 'horario')[:10]
        
        serializer = self.get_serializer(agendamentos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """Retorna estatísticas do dashboard"""
        hoje = date.today()
        primeiro_dia_mes = hoje.replace(day=1)
        qs = self.get_queryset()
        
        stats = {
            'agendamentos_hoje': qs.filter(data=hoje).count(),
            'agendamentos_mes': qs.filter(
                data__gte=primeiro_dia_mes,
                data__lte=hoje
            ).count(),
            'receita_mensal': float(
                qs.filter(
                    data__gte=primeiro_dia_mes,
                    data__lte=hoje,
                    status='concluido'
                ).aggregate(total=Sum('valor'))['total'] or 0
            ),
            'clientes_ativos': Cliente.objects.filter(is_active=True).count(),
            'procedimentos_ativos': Procedimento.objects.filter(is_active=True).count()
        }
        
        return Response(stats)

    @action(detail=False, methods=['get'], throttle_classes=[DashboardRateThrottle])
    def dashboard(self, request):
        """
        Retorna estatísticas + próximos agendamentos em uma única resposta.
        Cached por 60s para reduzir carga no banco.
        """
        loja_id = get_current_loja_id()
        cache_key = f'clinica:dashboard:{loja_id}'
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        hoje = date.today()
        primeiro_dia_mes = hoje.replace(day=1)
        qs = self.get_queryset()

        stats = {
            'agendamentos_hoje': qs.filter(data=hoje).count(),
            'agendamentos_mes': qs.filter(data__gte=primeiro_dia_mes, data__lte=hoje).count(),
            'receita_mensal': float(
                qs.filter(
                    data__gte=primeiro_dia_mes,
                    data__lte=hoje,
                    status='concluido'
                ).aggregate(total=Sum('valor'))['total'] or 0
            ),
            'clientes_ativos': Cliente.objects.filter(is_active=True).count(),
            'procedimentos_ativos': Procedimento.objects.filter(is_active=True).count(),
        }

        agendamentos = qs.filter(
            data__gte=hoje,
            status__in=['agendado', 'confirmado', 'em_atendimento']
        ).order_by('data', 'horario')[:10]
        serializer = self.get_serializer(agendamentos, many=True)

        payload = {
            'estatisticas': stats,
            'proximos': serializer.data,
        }
        cache.set(cache_key, payload, 60)
        return Response(payload)


class BloqueioAgendaViewSet(BaseModelViewSet):
    serializer_class = BloqueioAgendaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retorna bloqueios filtrados por loja, data e profissional."""
        loja_id = get_current_loja_id()
        tenant_db = get_current_tenant_db()

        if not loja_id:
            logger.warning('BloqueioAgendaViewSet: nenhuma loja no contexto')
            return BloqueioAgenda.objects.none()

        queryset = BloqueioAgenda.objects.all()
        if tenant_db and tenant_db != 'default':
            queryset = queryset.using(tenant_db)

        queryset = queryset.filter(loja_id=loja_id, is_active=True).select_related('profissional')

        params = getattr(self.request, 'query_params', self.request.GET)
        data_inicio_str = params.get('data_inicio')
        data_fim_str = params.get('data_fim')
        profissional_id = params.get('profissional_id')

        if data_inicio_str and data_fim_str:
            try:
                data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
                data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                data_inicio = data_fim = None
            if data_inicio is not None and data_fim is not None:
                queryset = queryset.filter(
                    data_inicio__lte=data_fim,
                    data_fim__gte=data_inicio,
                )

        if profissional_id:
            queryset = queryset.filter(Q(profissional_id=profissional_id) | Q(profissional__isnull=True))

        logger.debug('BloqueioAgendaViewSet: loja_id=%s, tenant_db=%s', loja_id, tenant_db)
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Sobrescreve create para logar erros de validação."""
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            logger.error('BloqueioAgenda: erro ao criar bloqueio: %s', e)
            raise
    
    def perform_create(self, serializer):
        """Preenche automaticamente o loja_id do contexto."""
        loja_id = get_current_loja_id()
        bloqueio = serializer.save(loja_id=loja_id)
        logger.debug('BloqueioAgenda criado: id=%s loja_id=%s', bloqueio.id, loja_id)
        return bloqueio


class ConsultaViewSet(BaseModelViewSet):
    serializer_class = ConsultaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Usar loja_id do header da requisição (não depender de thread-local em produção)
        loja_id = self.request.headers.get('X-Loja-ID') or getattr(
            self.request, 'META', {}
        ).get('HTTP_X_LOJA_ID')
        if not loja_id:
            loja_id = get_current_loja_id()
        if not loja_id:
            return Consulta.objects.none()
        try:
            loja_id = int(loja_id)
        except (ValueError, TypeError):
            return Consulta.objects.none()

        # Filtrar explicitamente por loja_id (all_without_filter + filter evita 404 em DELETE)
        base = Consulta.objects.all_without_filter().filter(loja_id=loja_id).select_related(
            'cliente', 'profissional', 'procedimento', 'agendamento'
        )

        params = getattr(self.request, 'query_params', self.request.GET)
        if params.get('cliente_id'):
            base = base.filter(cliente_id=params.get('cliente_id'))
        if params.get('profissional_id'):
            base = base.filter(profissional_id=params.get('profissional_id'))
        if params.get('status'):
            base = base.filter(status=params.get('status'))
        
        # Filtro para mostrar apenas consultas cujo agendamento foi confirmado
        if params.get('agendamento_confirmado') == 'true':
            base = base.filter(agendamento__status__in=['confirmado', 'em_atendimento', 'concluido'])

        return base

    @action(detail=True, methods=['post'])
    def iniciar_consulta(self, request, pk=None):
        """Inicia uma consulta (muda status para em_andamento)"""
        consulta = self.get_object()
        
        if consulta.status != 'agendada':
            return Response(
                {'error': 'Consulta deve estar agendada para ser iniciada'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        consulta.status = 'em_andamento'
        consulta.data_inicio = timezone.now()
        consulta.save()
        
        serializer = self.get_serializer(consulta)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def finalizar_consulta(self, request, pk=None):
        """Finaliza uma consulta (muda status para concluida)"""
        consulta = self.get_object()
        
        if consulta.status != 'em_andamento':
            return Response(
                {'error': 'Consulta deve estar em andamento para ser finalizada'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        consulta.status = 'concluida'
        consulta.data_fim = timezone.now()
        
        # Atualizar dados do pagamento se fornecidos
        valor_pago = request.data.get('valor_pago')
        forma_pagamento = request.data.get('forma_pagamento')
        observacoes = request.data.get('observacoes_gerais')
        
        if valor_pago is not None:
            consulta.valor_pago = valor_pago
        if forma_pagamento:
            consulta.forma_pagamento = forma_pagamento
        if observacoes:
            consulta.observacoes_gerais = observacoes
        
        consulta.save()
        
        # Atualizar status do agendamento
        consulta.agendamento.status = 'concluido'
        consulta.agendamento.save()
        
        serializer = self.get_serializer(consulta)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def sync_from_agendamentos(self, request):
        """
        Cria Consulta para Agendamentos que ainda não têm.
        Assim agendamentos já cadastrados passam a aparecer na Lista de Consultas.
        """
        loja_id = get_current_loja_id()
        if not loja_id:
            return Response(
                {'error': 'Contexto de loja não definido (X-Loja-ID)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Agendamentos da loja que ainda não têm Consulta
        agendamentos_sem_consulta = Agendamento.objects.filter(
            loja_id=loja_id
        ).exclude(
            id__in=Consulta.objects.values_list('agendamento_id', flat=True)
        )

        criadas = 0
        for ag in agendamentos_sem_consulta:
            Consulta.objects.get_or_create(
                agendamento=ag,
                defaults={
                    'cliente_id': ag.cliente_id,
                    'profissional_id': ag.profissional_id,
                    'procedimento_id': ag.procedimento_id,
                    'status': 'agendada',
                    'valor_consulta': ag.valor,
                    'loja_id': loja_id,
                }
            )
            criadas += 1

        return Response({'criadas': criadas, 'message': f'{criadas} consulta(s) criada(s) a partir de agendamentos.'})

    @action(detail=False, methods=['get'])
    def em_andamento(self, request):
        """Retorna consultas em andamento"""
        consultas = self.get_queryset().filter(status='em_andamento')
        serializer = self.get_serializer(consultas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def hoje(self, request):
        """Retorna consultas de hoje"""
        hoje = date.today()
        consultas = self.get_queryset().filter(agendamento__data=hoje)
        serializer = self.get_serializer(consultas, many=True)
        return Response(serializer.data)
