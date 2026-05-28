from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
import logging

from core.views import BaseModelViewSet
from .models import (
    Vendedor,
    Oportunidade,
    ProdutoServico,
    CategoriaProdutoServico,
    OportunidadeItem,
    Proposta,
    Contrato,
)
from .serializers import (
    VendedorSerializer,
    ProdutoServicoSerializer,
    CategoriaProdutoServicoSerializer,
    OportunidadeItemSerializer,
)
from tenants.middleware import get_current_loja_id
from .mixins import CRMPermissionMixin, VendedorFilterMixin, CacheInvalidationMixin
from .decorators import require_admin_access
from .vendedor_admin_service import (
    aplicar_cache_control_sem_store,
    ajustar_lista_vendedores_com_admin,
    listar_grupos_crm_disponiveis,
    reenviar_senha_administrador_loja,
    reenviar_senha_vendedor,
    resposta_vendedor_me,
)

from .views_common import (
    CRMPagination,
    LojaScopedCatalogMixin,
    filtrar_ativo_query_param,
    filtrar_queryset_por_query_params,
)

logger = logging.getLogger(__name__)


class VendedorViewSet(CRMPermissionMixin, BaseModelViewSet):
    queryset = Vendedor.objects.all()
    serializer_class = VendedorSerializer
    pagination_class = CRMPagination  # ✅ OTIMIZAÇÃO: Paginação

    def get_queryset(self):
        """✅ OTIMIZAÇÃO: Anotar tem_acesso para evitar N+1 queries"""
        qs = super().get_queryset()
        
        # Anotar se vendedor tem acesso (evita N+1)
        # IMPORTANTE: VendedorUsuario está no banco 'default', não no schema isolado
        # Não podemos usar Exists() cross-database, então removemos a anotação aqui
        # e fazemos a verificação no serializer ou no método list()
        
        if hasattr(Vendedor, 'is_active'):
            return qs.filter(is_active=True)
        return qs

    @require_admin_access('Vendedores não têm permissão para acessar configurações de funcionários.')
    def list(self, request, *args, **kwargs):
        loja_id = get_current_loja_id()
        for attempt in range(2):
            try:
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
            except Exception as e:
                from django.db.utils import ProgrammingError, OperationalError
                if isinstance(e, (ProgrammingError, OperationalError)) and attempt == 0:
                    from superadmin.models import Loja
                    from .schema_service import configurar_schema_crm_loja
                    loja_id = get_current_loja_id()
                    loja = Loja.objects.filter(id=loja_id).select_related('tipo_loja').first()
                    if loja and configurar_schema_crm_loja(loja):
                        continue
                raise

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
        # Impedir exclusão de vendedor admin (legacy: is_admin=True)
        instance = self.get_object()
        if instance.is_admin:
            return Response(
                {'detail': 'O vendedor administrador não pode ser excluído.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Retorna informações do vendedor logado."""
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
        """Reenvia senha provisória do administrador (Loja.owner)."""
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
        """Gera nova senha provisória e envia por e-mail. Funciona para vendedores e para o admin (owner)."""
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
        """Lista grupos disponíveis para atribuir a vendedores."""
        return Response(listar_grupos_crm_disponiveis())


class CategoriaProdutoServicoViewSet(LojaScopedCatalogMixin, BaseModelViewSet):
    """CRUD de categorias para organizar produtos e serviços."""
    queryset = CategoriaProdutoServico.objects.select_related('loja').all()
    serializer_class = CategoriaProdutoServicoSerializer
    pagination_class = CRMPagination
    loja_catalog_model = CategoriaProdutoServico
    loja_catalog_label = 'CategoriaProdutoServicoViewSet'

    def get_queryset(self):
        qs = self.get_loja_catalog_base_qs()
        return filtrar_ativo_query_param(qs, self.request)


class ProdutoServicoViewSet(LojaScopedCatalogMixin, BaseModelViewSet):
    """CRUD de produtos e serviços para uso em oportunidades."""
    queryset = ProdutoServico.objects.select_related('loja', 'categoria').all()
    serializer_class = ProdutoServicoSerializer
    pagination_class = CRMPagination
    loja_catalog_model = ProdutoServico
    loja_catalog_label = 'ProdutoServicoViewSet'

    def get_queryset(self):
        qs = self.get_loja_catalog_base_qs()
        qs = filtrar_ativo_query_param(qs, self.request)
        qs = filtrar_queryset_por_query_params(qs, self.request, {'tipo': 'tipo'})
        sem_cat = self.request.query_params.get('sem_categoria')
        if sem_cat and str(sem_cat).lower() in ('1', 'true', 'yes'):
            return qs.filter(categoria__isnull=True)
        return filtrar_queryset_por_query_params(qs, self.request, {'categoria': 'categoria_id'})


class OportunidadeItemViewSet(CacheInvalidationMixin, VendedorFilterMixin, BaseModelViewSet):
    """Itens (produtos/serviços) de uma oportunidade."""
    queryset = OportunidadeItem.objects.select_related('oportunidade', 'produto_servico').all()
    serializer_class = OportunidadeItemSerializer
    pagination_class = CRMPagination

    vendedor_filter_field = 'oportunidade__vendedor_id'
    vendedor_filter_related = []
    
    # Configuração do CacheInvalidationMixin
    cache_keys = ['oportunidades', 'dashboard']

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related('oportunidade', 'produto_servico')
        return filtrar_queryset_por_query_params(
            qs,
            self.request,
            {'oportunidade_id': 'oportunidade_id'},
        )

    def _recalcular_valor_oportunidade(self, oportunidade_id):
        """Recalcula valor da oportunidade e sincroniza propostas/contratos em rascunho."""
        from django.db.models import Sum, F
        itens = OportunidadeItem.objects.filter(oportunidade_id=oportunidade_id)
        total = itens.aggregate(
            total=Sum(F('quantidade') * F('preco_unitario'))
        )['total'] or 0
        Oportunidade.objects.filter(id=oportunidade_id).update(valor=total)
        # Sincronizar propostas e contratos (todas que não estão canceladas/rejeitadas)
        Proposta.objects.filter(oportunidade_id=oportunidade_id).exclude(status__in=['cancelada', 'rejeitada']).update(valor_total=total)
        Contrato.objects.filter(oportunidade_id=oportunidade_id).exclude(status='cancelado').update(valor_total=total)

    def perform_create(self, serializer):
        serializer.save()
        self._recalcular_valor_oportunidade(serializer.instance.oportunidade_id)
        self._invalidate_caches()

    def perform_update(self, serializer):
        serializer.save()
        self._recalcular_valor_oportunidade(serializer.instance.oportunidade_id)
        self._invalidate_caches()

    def perform_destroy(self, instance):
        oportunidade_id = instance.oportunidade_id
        instance.delete()
        self._recalcular_valor_oportunidade(oportunidade_id)
        self._invalidate_caches()


# ===========================================================================
# Re-exports para compatibilidade com urls.py
# Funções movidas para arquivos separados (refatoração)
# ===========================================================================
from .crm_config_helpers import get_crm_config_for_loja as _get_crm_config_for_loja  # noqa: F401, E402
from .views_config import (  # noqa: F401, E402
    _empty_dashboard_response,
    crm_me,
    dashboard_data,
    WhatsAppConfigView,
    LoginConfigView,
    crm_busca,
    crm_config,
    crm_config_asaas_test,
    crm_config_issnet_test,
)
from .views_relatorios import gerar_relatorio  # noqa: F401, E402
from .views_assinatura_publica import AssinaturaPublicaView, AssinaturaPdfView  # noqa: F401, E402
from .views_cadastros import ContaViewSet, ContatoViewSet, LeadViewSet  # noqa: F401, E402
from .views_documentos import (  # noqa: F401, E402
    ContratoTemplateViewSet,
    ContratoViewSet,
    PropostaTemplateViewSet,
    PropostaViewSet,
)
from .views_pipelines import AtividadeViewSet, OportunidadeViewSet  # noqa: F401, E402
