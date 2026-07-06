import logging

from core.views import BaseModelViewSet
from .models import (
    Oportunidade,
    ProdutoServico,
    CategoriaProdutoServico,
    OportunidadeItem,
    Proposta,
    Contrato,
)
from .serializers import (
    ProdutoServicoSerializer,
    CategoriaProdutoServicoSerializer,
    OportunidadeItemSerializer,
)
from .mixins import VendedorFilterMixin, CacheInvalidationMixin, CrmGranularPermissionMixin
from .views_common import (
    CRMPagination,
    LojaScopedCatalogMixin,
    filtrar_ativo_query_param,
    filtrar_queryset_por_query_params,
)

logger = logging.getLogger(__name__)


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


class ProdutoServicoViewSet(CrmGranularPermissionMixin, LojaScopedCatalogMixin, BaseModelViewSet):
    """CRUD de produtos e serviços para uso em oportunidades."""
    queryset = ProdutoServico.objects.select_related('loja', 'categoria').all()
    serializer_class = ProdutoServicoSerializer
    pagination_class = CRMPagination
    loja_catalog_model = ProdutoServico
    loja_catalog_label = 'ProdutoServicoViewSet'
    crm_permission_model = 'produtoservico'

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
# ===========================================================================
from .crm_config_helpers import get_crm_config_for_loja as _get_crm_config_for_loja  # noqa: F401, E402
from .views_config import (  # noqa: F401, E402
    _empty_dashboard_response,
    crm_me,
    dashboard_data,
    WhatsAppConfigView,
    CRMWhatsAppConnectionStatusView,
    CRMWhatsAppConnectView,
    CRMWhatsAppDisconnectView,
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
from .views_pipelines import AtividadeViewSet, OportunidadeNotaViewSet, OportunidadeViewSet  # noqa: F401, E402
from .views_vendedor import VendedorViewSet  # noqa: F401, E402
