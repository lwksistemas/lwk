"""Utilitários compartilhados entre ViewSets do CRM."""
import logging

from rest_framework.pagination import PageNumberPagination

from tenants.middleware import ensure_loja_context, get_current_loja_id

logger = logging.getLogger(__name__)


class CRMPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


def aplicar_cache_control_sem_store(response):
    """Evita cache de listagens CRM no navegador (dados por loja/vendedor)."""
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


def filtrar_queryset_por_query_params(queryset, request, param_field_map: dict[str, str]):
    """Aplica filtros opcionais ?param=valor como queryset.filter(field=valor)."""
    for param, field in param_field_map.items():
        value = request.query_params.get(param)
        if value:
            queryset = queryset.filter(**{field: value})
    return queryset


class CRMNoCacheListMixin:
    """Mixin para list() sem cache HTTP (padrão cadastros CRM)."""

    def list(self, request, *args, **kwargs):
        return aplicar_cache_control_sem_store(super().list(request, *args, **kwargs))


def filtrar_ativo_query_param(queryset, request, param='ativo', field='ativo'):
    """Filtra ?ativo=true|false quando o parâmetro está presente."""
    ativo = request.query_params.get(param)
    if ativo is not None:
        return queryset.filter(**{field: ativo.lower() == 'true'})
    return queryset


class LojaScopedCatalogMixin:
    """
    Catálogo por loja (CategoriaProdutoServico, ProdutoServico).
    perform_create com loja_id e queryset base filtrado por loja.
    """

    loja_catalog_model = None
    loja_catalog_label = 'LojaScopedCatalogMixin'

    def _ensure_loja_context(self):
        if hasattr(self, 'request') and self.request:
            ensure_loja_context(self.request)

    def perform_create(self, serializer):
        self._ensure_loja_context()
        loja_id = get_current_loja_id()
        if loja_id:
            serializer.save(loja_id=loja_id)
        else:
            serializer.save()

    def get_loja_catalog_base_qs(self):
        self._ensure_loja_context()
        loja_id = get_current_loja_id()
        if not loja_id:
            logger.warning('[%s] Acesso sem loja_id no contexto', self.loja_catalog_label)
            return self.loja_catalog_model.objects.none()
        return self.loja_catalog_model.objects.filter(loja_id=loja_id)
