"""ViewSet de vendedores / funcionários CRM."""
import logging

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.views import BaseModelViewSet
from tenants.middleware import get_current_loja_id

from .decorators import require_admin_access
from .mixins import CRMPermissionMixin, CRMSchemaRecoveryMixin
from .models import Vendedor
from .serializers import VendedorSerializer
from .vendedor_admin_service import (
    ajustar_lista_vendedores_com_admin,
    aplicar_cache_control_sem_store,
    listar_grupos_crm_disponiveis,
    reenviar_senha_administrador_loja,
    reenviar_senha_vendedor,
    resposta_vendedor_me,
)
from .vendedor_permissoes_service import listar_permissoes_crm_disponiveis
from .views_common import CRMPagination

logger = logging.getLogger(__name__)


class VendedorViewSet(CRMSchemaRecoveryMixin, CRMPermissionMixin, BaseModelViewSet):
    queryset = Vendedor.objects.all()
    serializer_class = VendedorSerializer
    pagination_class = CRMPagination

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(Vendedor, 'is_active'):
            return qs.filter(is_active=True)
        return qs

    @require_admin_access('Vendedores não têm permissão para acessar configurações de funcionários.')
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        loja_id = get_current_loja_id()
        if loja_id:
            from superadmin.models import Loja

            try:
                loja = Loja.objects.select_related('owner').get(id=loja_id)
                data = response.data
                results = list(
                    data.get('results', []) if isinstance(data, dict) else (data or [])
                )
                results = ajustar_lista_vendedores_com_admin(
                    loja,
                    loja_id,
                    results,
                    serialize_vendedor=lambda v: self.get_serializer(v).data,
                )
                if isinstance(data, dict):
                    response.data['results'] = results
                    response.data['count'] = len(results)
                else:
                    response.data = results
            except Loja.DoesNotExist:
                pass
        aplicar_cache_control_sem_store(response)
        return response

    @require_admin_access('Vendedores não têm permissão para acessar configurações de funcionários.')
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @require_admin_access('Vendedores não têm permissão para acessar configurações de funcionários.')
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @require_admin_access('Vendedores não têm permissão para acessar configurações de funcionários.')
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @require_admin_access('Vendedores não têm permissão para acessar configurações de funcionários.')
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @require_admin_access('Vendedores não têm permissão para acessar configurações de funcionários.')
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_admin:
            return Response(
                {'detail': 'O vendedor administrador não pode ser excluído.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def me(self, request):
        loja_id = get_current_loja_id()
        if not loja_id:
            return Response(
                {'detail': 'Contexto de loja não encontrado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return resposta_vendedor_me(request, loja_id)

    @action(detail=False, methods=['post'])
    @require_admin_access('Vendedores não têm permissão para acessar configurações de funcionários.')
    def reenviar_senha_administrador(self, request):
        loja_id = get_current_loja_id()
        if not loja_id:
            return Response(
                {'detail': 'Contexto de loja não encontrado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        payload, erro, http_status = reenviar_senha_administrador_loja(loja_id)
        if erro:
            return Response({'detail': erro}, status=http_status)
        return Response(payload, status=http_status)

    @action(detail=True, methods=['post'])
    @require_admin_access('Vendedores não têm permissão para acessar configurações de funcionários.')
    def reenviar_senha(self, request, pk=None):
        loja_id = get_current_loja_id()
        if not loja_id:
            return Response(
                {'detail': 'Contexto de loja não encontrado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        payload, erro, http_status = reenviar_senha_vendedor(loja_id, self.get_object())
        if erro:
            return Response({'detail': erro}, status=http_status)
        return Response(payload, status=http_status)

    @action(detail=False, methods=['get'])
    @require_admin_access('Vendedores não têm permissão para acessar configurações de funcionários.')
    def grupos_disponiveis(self, request):
        return Response(listar_grupos_crm_disponiveis())

    @action(detail=False, methods=['get'], url_path='permissoes_disponiveis')
    @require_admin_access('Vendedores não têm permissão para acessar configurações de funcionários.')
    def permissoes_disponiveis(self, request):
        return Response(listar_permissoes_crm_disponiveis())
