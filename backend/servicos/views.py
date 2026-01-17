from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum
from datetime import date
from .models import Categoria, Servico, Cliente, Profissional, Agendamento, OrdemServico, Orcamento, Funcionario
from .serializers import (
    CategoriaSerializer, ServicoSerializer, ClienteSerializer,
    ProfissionalSerializer, AgendamentoSerializer, OrdemServicoSerializer,
    OrcamentoSerializer, FuncionarioSerializer
)


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [IsAuthenticated]


class ServicoViewSet(viewsets.ModelViewSet):
    queryset = Servico.objects.all()
    serializer_class = ServicoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        categoria_id = self.request.query_params.get('categoria_id')
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]


class ProfissionalViewSet(viewsets.ModelViewSet):
    queryset = Profissional.objects.all()
    serializer_class = ProfissionalSerializer
    permission_classes = [IsAuthenticated]


class AgendamentoViewSet(viewsets.ModelViewSet):
    queryset = Agendamento.objects.all()
    serializer_class = AgendamentoSerializer
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
    def proximos(self, request):
        """Próximos agendamentos"""
        hoje = date.today()
        agendamentos = self.queryset.filter(
            data__gte=hoje,
            status__in=['agendado', 'confirmado']
        ).order_by('data', 'horario')[:10]
        serializer = self.get_serializer(agendamentos, many=True)
        return Response(serializer.data)


class OrdemServicoViewSet(viewsets.ModelViewSet):
    queryset = OrdemServico.objects.all()
    serializer_class = OrdemServicoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset

    @action(detail=False, methods=['get'])
    def abertas(self, request):
        """Ordens de serviço abertas"""
        ordens = self.queryset.filter(status__in=['aberta', 'em_andamento'])
        serializer = self.get_serializer(ordens, many=True)
        return Response(serializer.data)


class OrcamentoViewSet(viewsets.ModelViewSet):
    queryset = Orcamento.objects.all()
    serializer_class = OrcamentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset

    @action(detail=False, methods=['get'])
    def pendentes(self, request):
        """Orçamentos pendentes"""
        orcamentos = self.queryset.filter(status='pendente')
        serializer = self.get_serializer(orcamentos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """Estatísticas do dashboard"""
        hoje = date.today()
        
        # Serviços ativos
        servicos_ativos = OrdemServico.objects.filter(
            status__in=['aberta', 'em_andamento']
        ).count()
        
        # Clientes
        clientes = Cliente.objects.filter(is_active=True).count()
        
        # Agendamentos
        agendamentos = Agendamento.objects.filter(
            data__gte=hoje,
            status__in=['agendado', 'confirmado']
        ).count()
        
        # Receita do mês
        primeiro_dia_mes = hoje.replace(day=1)
        receita = OrdemServico.objects.filter(
            data_conclusao__gte=primeiro_dia_mes,
            data_conclusao__lte=hoje,
            status='concluida'
        ).aggregate(total=Sum('valor_total'))['total'] or 0
        
        return Response({
            'servicos_ativos': servicos_ativos,
            'clientes': clientes,
            'agendamentos': agendamentos,
            'receita': float(receita)
        })


class FuncionarioViewSet(viewsets.ModelViewSet):
    queryset = Funcionario.objects.all()
    serializer_class = FuncionarioSerializer
    permission_classes = [IsAuthenticated]
