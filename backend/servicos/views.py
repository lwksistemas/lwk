from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum
from datetime import date
from core.views import BaseModelViewSet
from .models import Categoria, Servico, Cliente, Profissional, Agendamento, OrdemServico, Orcamento, Funcionario
from .serializers import (
    CategoriaSerializer, ServicoSerializer, ClienteSerializer,
    ProfissionalSerializer, AgendamentoSerializer, OrdemServicoSerializer,
    OrcamentoSerializer, FuncionarioSerializer
)


class CategoriaViewSet(BaseModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer


class ServicoViewSet(BaseModelViewSet):
    queryset = Servico.objects.all()
    serializer_class = ServicoSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        categoria_id = self.request.query_params.get('categoria_id')
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)
        return queryset


class ClienteViewSet(BaseModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer


class ProfissionalViewSet(BaseModelViewSet):
    queryset = Profissional.objects.all()
    serializer_class = ProfissionalSerializer


class FuncionarioViewSet(BaseModelViewSet):
    queryset = Funcionario.objects.all()
    serializer_class = FuncionarioSerializer


class AgendamentoViewSet(BaseModelViewSet):
    queryset = Agendamento.objects.all()
    serializer_class = AgendamentoSerializer


class OrdemServicoViewSet(BaseModelViewSet):
    queryset = OrdemServico.objects.all()
    serializer_class = OrdemServicoSerializer


class OrcamentoViewSet(BaseModelViewSet):
    queryset = Orcamento.objects.all()
    serializer_class = OrcamentoSerializer
