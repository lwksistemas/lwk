from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import date, datetime, timedelta
from core.views import BaseModelViewSet
from .models import (
    Cliente, Profissional, Procedimento, Agendamento, Funcionario,
    ProtocoloProcedimento, EvolucaoPaciente, AnamnesesTemplate, Anamnese,
    HorarioFuncionamento, BloqueioAgenda, Consulta
)
from .serializers import (
    ClienteSerializer, ProfissionalSerializer, ProcedimentoSerializer,
    AgendamentoSerializer, FuncionarioSerializer, ProtocoloProcedimentoSerializer,
    EvolucaoPacienteSerializer, AnamnesesTemplateSerializer, AnamneseSerializer,
    HorarioFuncionamentoSerializer, BloqueioAgendaSerializer, ClienteBuscaSerializer,
    ConsultaSerializer
)


class ClienteViewSet(BaseModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def buscar(self, request):
        """Busca clientes por nome, telefone ou email"""
        params = getattr(request, 'query_params', request.GET)
        query = params.get('q', '')
        if len(query) < 2:
            return Response([])
        
        clientes = self.queryset.filter(
            Q(nome__icontains=query) |
            Q(telefone__icontains=query) |
            Q(email__icontains=query)
        )[:10]
        
        serializer = ClienteBuscaSerializer(clientes, many=True)
        return Response(serializer.data)


class ProfissionalViewSet(BaseModelViewSet):
    queryset = Profissional.objects.all()
    serializer_class = ProfissionalSerializer
    permission_classes = [IsAuthenticated]


class ProcedimentoViewSet(BaseModelViewSet):
    queryset = Procedimento.objects.all()
    serializer_class = ProcedimentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = getattr(self.request, 'query_params', self.request.GET)
        categoria = params.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        return queryset


class ProtocoloProcedimentoViewSet(BaseModelViewSet):
    queryset = ProtocoloProcedimento.objects.all()
    serializer_class = ProtocoloProcedimentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = getattr(self.request, 'query_params', self.request.GET)
        procedimento_id = params.get('procedimento_id')
        if procedimento_id:
            queryset = queryset.filter(procedimento_id=procedimento_id)
        return queryset


class AgendamentoViewSet(BaseModelViewSet):
    queryset = Agendamento.objects.select_related('cliente', 'profissional', 'procedimento')
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

    @action(detail=False, methods=['get'])
    def calendario(self, request):
        """Retorna agendamentos para visualização em calendário"""
        params = getattr(request, 'query_params', request.GET)
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
        agendamentos = self.queryset.filter(
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
        
        stats = {
            'agendamentos_hoje': self.queryset.filter(data=hoje).count(),
            'agendamentos_mes': self.queryset.filter(
                data__gte=primeiro_dia_mes,
                data__lte=hoje
            ).count(),
            'receita_mensal': float(
                self.queryset.filter(
                    data__gte=primeiro_dia_mes,
                    data__lte=hoje,
                    status='concluido'
                ).aggregate(total=Sum('valor'))['total'] or 0
            ),
            'clientes_ativos': Cliente.objects.filter(is_active=True).count(),
            'procedimentos_ativos': Procedimento.objects.filter(is_active=True).count()
        }
        
        return Response(stats)

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Retorna estatísticas + próximos agendamentos em uma única resposta (menos round-trips)."""
        hoje = date.today()
        primeiro_dia_mes = hoje.replace(day=1)
        qs = self.queryset

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
            status__in=['agendado', 'confirmado']
        ).order_by('data', 'horario')[:10]
        serializer = self.get_serializer(agendamentos, many=True)

        return Response({
            'estatisticas': stats,
            'proximos': serializer.data,
        })


class EvolucaoPacienteViewSet(BaseModelViewSet):
    queryset = EvolucaoPaciente.objects.select_related('cliente', 'profissional', 'agendamento')
    serializer_class = EvolucaoPacienteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        cliente_id = getattr(self.request, "query_params", self.request.GET).get('cliente_id')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        return queryset


class AnamnesesTemplateViewSet(BaseModelViewSet):
    queryset = AnamnesesTemplate.objects.select_related('procedimento')
    serializer_class = AnamnesesTemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        procedimento_id = getattr(self.request, "query_params", self.request.GET).get('procedimento_id')
        if procedimento_id:
            queryset = queryset.filter(procedimento_id=procedimento_id)
        return queryset


class AnamneseViewSet(BaseModelViewSet):
    queryset = Anamnese.objects.select_related('cliente', 'template', 'agendamento')
    serializer_class = AnamneseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        cliente_id = getattr(self.request, "query_params", self.request.GET).get('cliente_id')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        return queryset


class HorarioFuncionamentoViewSet(BaseModelViewSet):
    queryset = HorarioFuncionamento.objects.all()
    serializer_class = HorarioFuncionamentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(is_active=True).order_by('dia_semana')


class BloqueioAgendaViewSet(BaseModelViewSet):
    queryset = BloqueioAgenda.objects.select_related('profissional')
    serializer_class = BloqueioAgendaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = getattr(self.request, "query_params", self.request.GET)
        data_inicio = params.get('data_inicio')
        data_fim = params.get('data_fim')
        profissional_id = params.get('profissional_id')

        # Apenas bloqueios ativos
        queryset = queryset.filter(is_active=True)
        
        if data_inicio and data_fim:
            queryset = queryset.filter(
                data_inicio__lte=data_fim,
                data_fim__gte=data_inicio
            )

        # Se filtrar por profissional, incluir bloqueios do profissional E bloqueios globais (profissional null)
        if profissional_id:
            queryset = queryset.filter(Q(profissional_id=profissional_id) | Q(profissional__isnull=True))
        
        return queryset


class FuncionarioViewSet(BaseModelViewSet):
    queryset = Funcionario.objects.all()
    serializer_class = FuncionarioSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Garante isolamento por loja com validação extra de segurança
        """
        import logging
        logger = logging.getLogger(__name__)
        
        queryset = super().get_queryset()
        
        # Validação extra de segurança
        from tenants.middleware import get_current_loja_id
        loja_id = get_current_loja_id()
        
        if not loja_id:
            logger.critical("🚨 [FuncionarioViewSet] Tentativa de acesso sem loja_id no contexto")
            return queryset.none()
        
        # O filtro já é aplicado pelo LojaIsolationManager,
        # mas adicionar log para debug
        logger.info(f"✅ [FuncionarioViewSet] Filtrando funcionários por loja_id={loja_id}")
        logger.info(f"📊 [FuncionarioViewSet] Total de funcionários encontrados: {queryset.count()}")
        
        return queryset


class ConsultaViewSet(BaseModelViewSet):
    serializer_class = ConsultaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Usar loja_id do header da requisição (não depender de thread-local em produção)
        loja_id = self.request.headers.get('X-Loja-ID') or getattr(
            self.request, 'META', {}
        ).get('HTTP_X_LOJA_ID')
        if not loja_id:
            from tenants.middleware import get_current_loja_id
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
        from tenants.middleware import get_current_loja_id

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
        consultas = self.queryset.filter(status='em_andamento')
        serializer = self.get_serializer(consultas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def hoje(self, request):
        """Retorna consultas de hoje"""
        hoje = date.today()
        consultas = self.queryset.filter(agendamento__data=hoje)
        serializer = self.get_serializer(consultas, many=True)
        return Response(serializer.data)