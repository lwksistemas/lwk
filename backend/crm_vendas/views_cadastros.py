"""ViewSets de cadastros CRM: contas, leads e contatos."""
import logging

from rest_framework.decorators import action
from rest_framework.response import Response

from core.views import BaseModelViewSet
from tenants.middleware import get_current_loja_id
from .cache import CRMCacheManager
from .mixins import CacheInvalidationMixin, VendedorFilterMixin
from .models import Atividade, Conta, Contato, Lead, Vendedor
from .serializers import (
    AtividadeListSerializer,
    ContaSerializer,
    ContatoSerializer,
    LeadListSerializer,
    LeadSerializer,
)
from .utils import get_current_vendedor_id
from .views_common import CRMPagination

logger = logging.getLogger(__name__)


class ContaViewSet(CacheInvalidationMixin, BaseModelViewSet):
    queryset = Conta.objects.select_related('vendedor').prefetch_related('leads', 'contatos').all()
    serializer_class = ContaSerializer
    pagination_class = CRMPagination
    cache_keys = ['contas']

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related('vendedor').prefetch_related('leads', 'contatos')
        tipo = self.request.query_params.get('tipo')
        if tipo:
            if tipo == 'prestadora':
                qs = qs.filter(tipo__in=['prestadora', 'ambos'])
            elif tipo == 'cliente':
                qs = qs.filter(tipo__in=['cliente', 'ambos'])
            else:
                qs = qs.filter(tipo=tipo)
        return qs

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    def perform_create(self, serializer):
        vendedor_id = get_current_vendedor_id(self.request)
        if vendedor_id is not None:
            if Vendedor.objects.filter(id=vendedor_id).exists():
                serializer.save(vendedor_id=vendedor_id)
            else:
                logger.warning(
                    '[ContaViewSet.perform_create] vendedor_id=%s não existe no schema, '
                    'salvando conta sem vendedor',
                    vendedor_id,
                )
                serializer.save()
        else:
            serializer.save()
        self._invalidate_caches()

    @action(detail=True, methods=['get'])
    def atividades(self, request, pk=None):
        conta = self.get_object()
        atividades = Atividade.objects.filter(conta=conta).order_by('-data')[:50]
        serializer = AtividadeListSerializer(atividades, many=True)
        return Response(serializer.data)


class LeadViewSet(CacheInvalidationMixin, VendedorFilterMixin, BaseModelViewSet):
    queryset = Lead.objects.select_related('conta', 'vendedor').prefetch_related('oportunidades').all()
    serializer_class = LeadSerializer
    pagination_class = CRMPagination

    vendedor_filter_field = 'vendedor_id'
    vendedor_filter_related = ['oportunidades__vendedor_id']
    cache_keys = ['leads']

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
                        status = self.request.query_params.get('status')
                        if status:
                            qs = qs.filter(status=status)
                        origem = self.request.query_params.get('origem')
                        if origem:
                            qs = qs.filter(origem=origem)
                        return qs
                except Exception:
                    pass

        qs = self.filter_by_vendedor(qs)
        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)
        origem = self.request.query_params.get('origem')
        if origem:
            qs = qs.filter(origem=origem)
        return qs

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    def perform_create(self, serializer):
        vendedor_id = get_current_vendedor_id(self.request)
        if vendedor_id is not None:
            if Vendedor.objects.filter(id=vendedor_id).exists():
                serializer.save(vendedor_id=vendedor_id)
            else:
                logger.warning(
                    '[LeadViewSet.perform_create] vendedor_id=%s não existe no schema, '
                    'salvando lead sem vendedor',
                    vendedor_id,
                )
                serializer.save()
        else:
            serializer.save()
        self._invalidate_caches()


class ContatoViewSet(CacheInvalidationMixin, BaseModelViewSet):
    queryset = Contato.objects.select_related('conta').all()
    serializer_class = ContatoSerializer
    pagination_class = CRMPagination
    cache_keys = ['contatos']

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related('conta')
        conta_id = self.request.query_params.get('conta_id')
        if conta_id:
            qs = qs.filter(conta_id=conta_id)
        return qs

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
                except Exception:
                    pass

        self._invalidate_caches()
