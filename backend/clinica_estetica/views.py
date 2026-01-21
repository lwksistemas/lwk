from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import date, datetime, timedelta
from core.views import BaseModelViewSet
from .models import (
    Cliente, Profissional, Procedimento, Agendamento, Funcionario,
    ProtocoloProcedimento, EvolucaoPaciente, AnamnesesTemplate, Anamnese,
    HorarioFuncionamento, BloqueioAgenda
)
from .serializers import (
    ClienteSerializer, ProfissionalSerializer, ProcedimentoSerializer,
    AgendamentoSerializer, FuncionarioSerializer, ProtocoloProcedimentoSerializer,
    EvolucaoPacienteSerializer, AnamnesesTemplateSerializer, AnamneseSerializer,
    HorarioFuncionamentoSerializer, BloqueioAgendaSerializer, ClienteBuscaSerializer
)


class ClienteViewSet(BaseModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer

    @action(detail=False, methods=['get'])
    def buscar(self, request):
        """Busca clientes por nome, telefone ou email"""
        query = request.query_params.get('q', '')
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


class ProcedimentoViewSet(BaseModelViewSet):
    queryset = Procedimento.objects.all()
    serializer_class = ProcedimentoSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        categoria = self.request.query_params.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        return queryset


class ProtocoloProcedimentoViewSet(BaseModelViewSet):
    queryset = ProtocoloProcedimento.objects.all()
    serializer_class = ProtocoloProcedimentoSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        procedimento_id = self.request.query_params.get('procedimento_id')
        if procedimento_id:
            queryset = queryset.filter(procedimento_id=procedimento_id)
        return queryset


class AgendamentoViewSet(BaseModelViewSet):
    queryset = Agendamento.objects.select_related('cliente', 'profissional', 'procedimento')
    serializer_class = AgendamentoSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros
        data = self.request.query_params.get('data')
        if data:
            queryset = queryset.filter(data=data)
        
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        cliente_id = self.request.query_params.get('cliente_id')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        
        profissional_id = self.request.query_params.get('profissional_id')
        if profissional_id:
            queryset = queryset.filter(profissional_id=profissional_id)
        
        return queryset

    @action(detail=False, methods=['get'])
    def calendario(self, request):
        """Retorna agendamentos para visualização em calendário"""
        data_inicio = request.query_params.get('data_inicio')
        data_fim = request.query_params.get('data_fim')
        
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

    def get_queryset(self):
        queryset = super().get_queryset()
        cliente_id = self.request.query_params.get('cliente_id')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        return queryset


class AnamnesesTemplateViewSet(BaseModelViewSet):
    queryset = AnamnesesTemplate.objects.select_related('procedimento')
    serializer_class = AnamnesesTemplateSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        procedimento_id = self.request.query_params.get('procedimento_id')
        if procedimento_id:
            queryset = queryset.filter(procedimento_id=procedimento_id)
        return queryset


class AnamneseViewSet(BaseModelViewSet):
    queryset = Anamnese.objects.select_related('cliente', 'template', 'agendamento')
    serializer_class = AnamneseSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        cliente_id = self.request.query_params.get('cliente_id')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        return queryset


class HorarioFuncionamentoViewSet(BaseModelViewSet):
    queryset = HorarioFuncionamento.objects.all()
    serializer_class = HorarioFuncionamentoSerializer

    def get_queryset(self):
        return self.queryset.filter(is_active=True).order_by('dia_semana')


class BloqueioAgendaViewSet(BaseModelViewSet):
    queryset = BloqueioAgenda.objects.select_related('profissional')
    serializer_class = BloqueioAgendaSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        data_inicio = self.request.query_params.get('data_inicio')
        data_fim = self.request.query_params.get('data_fim')
        
        if data_inicio and data_fim:
            queryset = queryset.filter(
                data_inicio__lte=data_fim,
                data_fim__gte=data_inicio
            )
        
        return queryset


class FuncionarioViewSet(BaseModelViewSet):
    queryset = Funcionario.objects.all()
    serializer_class = FuncionarioSerializer