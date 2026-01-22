from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum, Q
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
    permission_classes = [permissions.AllowAny]  # Permitir acesso sem autenticação

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
    permission_classes = [permissions.AllowAny]  # Permitir acesso sem autenticação


class ProcedimentoViewSet(BaseModelViewSet):
    queryset = Procedimento.objects.all()
    serializer_class = ProcedimentoSerializer
    permission_classes = [permissions.AllowAny]  # Permitir acesso sem autenticação

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
    permission_classes = [permissions.AllowAny]  # Permitir acesso sem autenticação

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
    permission_classes = [permissions.AllowAny]  # Permitir acesso sem autenticação

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
        
        agendamentos = self.queryset.filter(
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


class EvolucaoPacienteViewSet(BaseModelViewSet):
    queryset = EvolucaoPaciente.objects.select_related('cliente', 'profissional', 'agendamento')
    serializer_class = EvolucaoPacienteSerializer
    permission_classes = [permissions.AllowAny]  # Permitir acesso sem autenticação

    def get_queryset(self):
        queryset = super().get_queryset()
        cliente_id = getattr(self.request, "query_params", self.request.GET).get('cliente_id')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        return queryset


class AnamnesesTemplateViewSet(BaseModelViewSet):
    queryset = AnamnesesTemplate.objects.select_related('procedimento')
    serializer_class = AnamnesesTemplateSerializer
    permission_classes = [permissions.AllowAny]  # Permitir acesso sem autenticação

    def get_queryset(self):
        queryset = super().get_queryset()
        procedimento_id = getattr(self.request, "query_params", self.request.GET).get('procedimento_id')
        if procedimento_id:
            queryset = queryset.filter(procedimento_id=procedimento_id)
        return queryset


class AnamneseViewSet(BaseModelViewSet):
    queryset = Anamnese.objects.select_related('cliente', 'template', 'agendamento')
    serializer_class = AnamneseSerializer
    permission_classes = [permissions.AllowAny]  # Permitir acesso sem autenticação

    def get_queryset(self):
        queryset = super().get_queryset()
        cliente_id = getattr(self.request, "query_params", self.request.GET).get('cliente_id')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        return queryset


class HorarioFuncionamentoViewSet(BaseModelViewSet):
    queryset = HorarioFuncionamento.objects.all()
    serializer_class = HorarioFuncionamentoSerializer
    permission_classes = [permissions.AllowAny]  # Permitir acesso sem autenticação

    def get_queryset(self):
        return self.queryset.filter(is_active=True).order_by('dia_semana')


class BloqueioAgendaViewSet(BaseModelViewSet):
    queryset = BloqueioAgenda.objects.select_related('profissional')
    serializer_class = BloqueioAgendaSerializer
    permission_classes = [permissions.AllowAny]  # Permitir acesso sem autenticação

    def get_queryset(self):
        queryset = super().get_queryset()
        data_inicio = getattr(self.request, "query_params", self.request.GET).get('data_inicio')
        data_fim = getattr(self.request, "query_params", self.request.GET).get('data_fim')
        
        if data_inicio and data_fim:
            queryset = queryset.filter(
                data_inicio__lte=data_fim,
                data_fim__gte=data_inicio
            )
        
        return queryset


class FuncionarioViewSet(BaseModelViewSet):
    queryset = Funcionario.objects.all()
    serializer_class = FuncionarioSerializer
    permission_classes = [permissions.AllowAny]  # Permitir acesso sem autenticação


class ConsultaViewSet(BaseModelViewSet):
    queryset = Consulta.objects.select_related('cliente', 'profissional', 'procedimento', 'agendamento')
    serializer_class = ConsultaSerializer
    permission_classes = [permissions.AllowAny]  # Permitir acesso sem autenticação

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Verificar se request tem query_params (DRF) ou GET (Django padrão)
        params = getattr(self.request, 'query_params', self.request.GET)
        
        # Filtros
        cliente_id = params.get('cliente_id')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        
        profissional_id = params.get('profissional_id')
        if profissional_id:
            queryset = queryset.filter(profissional_id=profissional_id)
        
        status = params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset

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