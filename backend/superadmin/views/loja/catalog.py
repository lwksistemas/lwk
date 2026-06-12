from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.core.management import call_command
from django.conf import settings
from django.db import transaction
from django.utils import timezone
import logging

from drf_spectacular.utils import extend_schema_view, extend_schema
from core.logging_utils import mask_email
from ...api_docs import (
    TIPO_LOJA_LIST_SCHEMA,
    TIPO_LOJA_CREATE_SCHEMA,
    PLANO_LIST_SCHEMA,
    LOJA_LIST_SCHEMA,
    LOJA_CREATE_SCHEMA,
    LOJA_DELETE_SCHEMA,
)
from ...models import (
    TipoLoja, PlanoAssinatura, Loja, FinanceiroLoja, ProfissionalUsuario,
)
from ...serializers import (
    TipoLojaSerializer, PlanoAssinaturaSerializer, LojaSerializer, LojaCreateSerializer,
)
from ..permissions import IsOwnerOrSuperAdmin, IsSuperAdmin

logger = logging.getLogger(__name__)

# ✅ ViewSets públicos para cadastro de lojas
class TipoLojaPublicoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet público para listar tipos de loja (somente leitura)
    Usado no formulário de cadastro público
    """
    serializer_class = TipoLojaSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    
    def get_queryset(self):
        return TipoLoja.objects.filter(is_active=True).order_by('nome')


class PlanoAssinaturaPublicoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet público para listar planos de assinatura (somente leitura)
    Usado no formulário de cadastro público
    """
    serializer_class = PlanoAssinaturaSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    
    def get_queryset(self):
        return PlanoAssinatura.objects.filter(is_active=True).order_by('preco_mensal')
    
    @action(detail=False, methods=['get'])
    def por_tipo(self, request):
        """Buscar planos por tipo de app (público)"""
        tipo_id = request.query_params.get('tipo_id')
        if tipo_id:
            planos = self.get_queryset().filter(tipos_loja__id=tipo_id)
            serializer = self.get_serializer(planos, many=True)
            return Response(serializer.data)
        return Response({'error': 'tipo_id é obrigatório'}, status=400)


@extend_schema_view(
    list=TIPO_LOJA_LIST_SCHEMA,
    create=TIPO_LOJA_CREATE_SCHEMA,
    retrieve=extend_schema(summary="Detalhes do Tipo de App", tags=["Tipos de App"]),
    update=extend_schema(summary="Atualizar Tipo de App", tags=["Tipos de App"]),
    partial_update=extend_schema(summary="Atualizar Parcialmente Tipo de App", tags=["Tipos de App"]),
    destroy=extend_schema(summary="Excluir Tipo de App", tags=["Tipos de App"]),
)
class TipoLojaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar Tipos de App.
    Tipos de App definem as funcionalidades e aparência de cada loja.
    """
    serializer_class = TipoLojaSerializer
    permission_classes = [IsSuperAdmin]
    
    def get_queryset(self):
        return TipoLoja.objects.prefetch_related('lojas', 'planos').all()


@extend_schema_view(
    list=PLANO_LIST_SCHEMA,
    create=extend_schema(summary="Criar Plano", tags=["Planos"]),
    retrieve=extend_schema(summary="Detalhes do Plano", tags=["Planos"]),
    update=extend_schema(summary="Atualizar Plano", tags=["Planos"]),
    partial_update=extend_schema(summary="Atualizar Parcialmente Plano", tags=["Planos"]),
    destroy=extend_schema(summary="Excluir Plano", tags=["Planos"]),
)
class PlanoAssinaturaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar Planos de Assinatura.
    Planos definem preços e limites para cada tipo de app.
    """
    serializer_class = PlanoAssinaturaSerializer
    permission_classes = [IsSuperAdmin]
    
    def get_queryset(self):
        return PlanoAssinatura.objects.prefetch_related('tipos_loja', 'lojas').all()

    def update(self, request, *args, **kwargs):
        """Permite atualização parcial via PUT (além do PATCH)."""
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def por_tipo(self, request):
        """Buscar planos por tipo de app (superadmin: ativos e inativos)."""
        tipo_id = request.query_params.get('tipo_id')
        if tipo_id:
            planos = self.get_queryset().filter(tipos_loja__id=tipo_id).distinct()
            serializer = self.get_serializer(planos, many=True)
            return Response(serializer.data)
        return Response({'error': 'tipo_id é obrigatório'}, status=400)
