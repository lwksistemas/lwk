from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import date
from .models import Cliente, Profissional, Procedimento, Agendamento, Funcionario
from .serializers import (
    ClienteSerializer, ProfissionalSerializer, ProcedimentoSerializer,
    AgendamentoSerializer, FuncionarioSerializer
)


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset


class ProfissionalViewSet(viewsets.ModelViewSet):
    queryset = Profissional.objects.all()
    serializer_class = ProfissionalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset


class ProcedimentoViewSet(viewsets.ModelViewSet):
    queryset = Procedimento.objects.all()
    serializer_class = ProcedimentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        categoria = self.request.query_params.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        return queryset


class AgendamentoViewSet(viewsets.ModelViewSet):
    queryset = Agendamento.objects.all()
    serializer_class = AgendamentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrar por data
        data = self.request.query_params.get('data')
        if data:
            queryset = queryset.filter(data=data)
        
        # Filtrar por status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filtrar por cliente
        cliente_id = self.request.query_params.get('cliente_id')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        
        # Filtrar por profissional
        profissional_id = self.request.query_params.get('profissional_id')
        if profissional_id:
            queryset = queryset.filter(profissional_id=profissional_id)
        
        return queryset

    @action(detail=False, methods=['get'])
    def proximos(self, request):
        """Retorna próximos agendamentos (hoje e futuros)"""
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
        
        # Agendamentos hoje
        agendamentos_hoje = Agendamento.objects.filter(data=hoje).count()
        
        # Clientes ativos
        clientes_ativos = Cliente.objects.filter(is_active=True).count()
        
        # Total de procedimentos
        procedimentos = Procedimento.objects.filter(is_active=True).count()
        
        # Receita mensal (agendamentos concluídos do mês atual)
        primeiro_dia_mes = hoje.replace(day=1)
        receita_mensal = Agendamento.objects.filter(
            data__gte=primeiro_dia_mes,
            data__lte=hoje,
            status='concluido'
        ).aggregate(total=Sum('valor'))['total'] or 0
        
        return Response({
            'agendamentos_hoje': agendamentos_hoje,
            'clientes_ativos': clientes_ativos,
            'procedimentos': procedimentos,
            'receita_mensal': float(receita_mensal)
        })


class FuncionarioViewSet(viewsets.ModelViewSet):
    queryset = Funcionario.objects.all()
    serializer_class = FuncionarioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset
