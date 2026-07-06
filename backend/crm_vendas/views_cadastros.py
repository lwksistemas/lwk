"""ViewSets de cadastros CRM: contas, leads e contatos."""
import logging

from rest_framework.decorators import action
from rest_framework.response import Response

from core.views import BaseModelViewSet
from tenants.middleware import get_current_loja_id
from .cache import CRMCacheManager
from .mixins import CacheInvalidationMixin, CrmGranularPermissionMixin, VendedorAutoAssignCreateMixin, VendedorFilterMixin
from .models import Atividade, Conta, Contato, Lead
from .serializers import (
    AtividadeListSerializer,
    ContaSerializer,
    ContatoSerializer,
    LeadListSerializer,
    LeadSerializer,
)
from .views_common import (
    CRMNoCacheListMixin,
    CRMPagination,
    filtrar_leads_por_documento,
    filtrar_queryset_por_documento,
    filtrar_queryset_por_query_params,
)

logger = logging.getLogger(__name__)


class ContaViewSet(
    CrmGranularPermissionMixin,
    CRMNoCacheListMixin,
    CacheInvalidationMixin,
    VendedorAutoAssignCreateMixin,
    VendedorFilterMixin,
    BaseModelViewSet,
):
    queryset = Conta.objects.select_related('vendedor').prefetch_related('leads', 'contatos').all()
    serializer_class = ContaSerializer
    pagination_class = CRMPagination
    vendedor_filter_field = 'vendedor_id'
    cache_keys = ['contas']
    crm_permission_model = 'conta'

    def get_queryset(self):
        qs = super().get_queryset()
        qs = self.filter_by_vendedor(qs)
        qs = qs.select_related('vendedor').prefetch_related('leads', 'contatos')
        tipo = self.request.query_params.get('tipo')
        if tipo:
            if tipo == 'prestadora':
                qs = qs.filter(tipo__in=['prestadora', 'ambos'])
            elif tipo == 'cliente':
                qs = qs.filter(tipo__in=['cliente', 'ambos'])
            else:
                qs = qs.filter(tipo=tipo)
        return filtrar_queryset_por_documento(qs, self.request, 'cnpj')

    vendedor_create_entity_label = 'conta'

    @action(detail=True, methods=['get'])
    def atividades(self, request, pk=None):
        conta = self.get_object()
        atividades = Atividade.objects.filter(conta=conta).order_by('-data')[:50]
        serializer = AtividadeListSerializer(atividades, many=True)
        return Response(serializer.data)


class LeadViewSet(
    CrmGranularPermissionMixin,
    CRMNoCacheListMixin,
    CacheInvalidationMixin,
    VendedorAutoAssignCreateMixin,
    VendedorFilterMixin,
    BaseModelViewSet,
):
    queryset = Lead.objects.select_related('conta', 'vendedor').prefetch_related('oportunidades').all()
    serializer_class = LeadSerializer
    pagination_class = CRMPagination

    vendedor_filter_field = 'vendedor_id'
    vendedor_filter_related = ['oportunidades__vendedor_id']
    cache_keys = ['leads']
    crm_permission_model = 'lead'

    def get_serializer_class(self):
        if self.action == 'list':
            return LeadListSerializer
        return LeadSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related('conta', 'vendedor', 'contato').prefetch_related(
            'oportunidades',
            'oportunidades__vendedor',
        )

        if self.action == 'retrieve':
            from superadmin.models import Loja

            loja_id = get_current_loja_id()
            if loja_id and self.request and self.request.user:
                try:
                    loja = Loja.objects.using('default').filter(id=loja_id).first()
                    if loja and loja.owner_id == self.request.user.id:
                        return filtrar_queryset_por_query_params(
                            qs,
                            self.request,
                            {'status': 'status', 'origem': 'origem'},
                        )
                except Exception as e:
                    logger.warning('crm_me: erro ao determinar loja_id=%s: %s', loja_id, e)
        qs = filtrar_queryset_por_query_params(
            qs,
            self.request,
            {'status': 'status', 'origem': 'origem'},
        )
        return filtrar_leads_por_documento(qs, self.request)

    vendedor_create_entity_label = 'lead'


class ContatoViewSet(CrmGranularPermissionMixin, CRMNoCacheListMixin, CacheInvalidationMixin, BaseModelViewSet):
    queryset = Contato.objects.select_related('conta').all()
    serializer_class = ContatoSerializer
    pagination_class = CRMPagination
    cache_keys = ['contatos']
    crm_permission_model = 'contato'

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related('conta')
        return filtrar_queryset_por_query_params(
            qs,
            self.request,
            {'conta_id': 'conta_id'},
        )

    def perform_update(self, serializer):
        instance_antes = self.get_object()
        nome_antes = instance_antes.nome
        email_antes = instance_antes.email
        telefone_antes = instance_antes.telefone

        instance = serializer.save()

        update_fields = {}
        if instance.nome != nome_antes:
            update_fields['nome'] = instance.nome
        if instance.email != email_antes:
            update_fields['email'] = instance.email or ''
        if instance.telefone != telefone_antes:
            update_fields['telefone'] = instance.telefone or ''

        if update_fields:
            updated = Lead.objects.filter(contato_id=instance.id).update(**update_fields)
            if updated:
                logger.info(
                    'Contato %s atualizado: propagados %s para %d Lead(s) vinculado(s).',
                    instance.id,
                    list(update_fields.keys()),
                    updated,
                )
                try:
                    CRMCacheManager.invalidate_dashboard(getattr(instance, 'loja_id', None))
                except Exception as e:
                    logger.warning('Falha ao invalidar cache dashboard contato_id=%s: %s', instance.id, e)

        self._invalidate_caches()
