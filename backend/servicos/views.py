from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from core.views import BaseModelViewSet
from .models import Categoria, Servico, Cliente, Profissional, Agendamento, OrdemServico, Orcamento, Funcionario
from .serializers import (
    CategoriaSerializer, ServicoSerializer, ClienteSerializer,
    ProfissionalSerializer, AgendamentoSerializer, OrdemServicoSerializer,
    OrcamentoSerializer, FuncionarioSerializer
)


class CategoriaViewSet(BaseModelViewSet):
    # Otimização: prefetch_related para servicos
    queryset = Categoria.objects.prefetch_related('servicos').all()
    serializer_class = CategoriaSerializer


class ServicoViewSet(BaseModelViewSet):
    # Otimização: select_related para categoria
    queryset = Servico.objects.select_related('categoria').all()
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
    
    def _ensure_owner_funcionario(self):
        """
        Garante que o administrador da loja exista como funcionário (aparece em Funcionários).
        
        NOTA: O app servicos NÃO usa LojaIsolationMixin, então este método
        não faz nada por enquanto. Implementar quando migrar para isolamento por loja.
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.debug("ℹ️ [FuncionarioViewSet SERVICOS] App servicos não usa isolamento por loja ainda")
        return
    
    def list(self, request, *args, **kwargs):
        self._ensure_owner_funcionario()
        return super().list(request, *args, **kwargs)
    
    def get_queryset(self):
        # IMPORTANTE: Garantir que admin existe antes de filtrar
        self._ensure_owner_funcionario()
        return super().get_queryset()


class AgendamentoViewSet(BaseModelViewSet):
    # Otimização: select_related
    queryset = Agendamento.objects.select_related('cliente', 'servico', 'profissional').all()
    serializer_class = AgendamentoSerializer


class OrdemServicoViewSet(BaseModelViewSet):
    # Otimização: select_related
    queryset = OrdemServico.objects.select_related('cliente', 'servico', 'profissional').all()
    serializer_class = OrdemServicoSerializer


class OrcamentoViewSet(BaseModelViewSet):
    # Otimização: select_related
    queryset = Orcamento.objects.select_related('cliente', 'servico').all()
    serializer_class = OrcamentoSerializer
