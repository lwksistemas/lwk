"""ViewSets de pipeline: oportunidades e atividades."""
import logging

from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.views import BaseModelViewSet
from tenants.middleware import get_current_loja_id, get_current_tenant_db
from .activities_google_sync import (
    sync_atividade_create,
    sync_atividade_delete,
    sync_atividade_update,
)
from .atividade_whatsapp_service import enviar_atividade_whatsapp
from .cache import CRMCacheManager
from .decorators import cache_list_response
from .mixins import CacheInvalidationMixin, VendedorFilterMixin
from .models import Atividade, Oportunidade, Vendedor
from .serializers import (
    AtividadeListSerializer,
    AtividadeSerializer,
    OportunidadeSerializer,
)
from .services import OportunidadeService
from .utils import get_current_vendedor_id
from .views_common import CRMPagination, aplicar_cache_control_sem_store, filtrar_queryset_por_query_params

logger = logging.getLogger(__name__)


class OportunidadeViewSet(CacheInvalidationMixin, VendedorFilterMixin, BaseModelViewSet):
    queryset = Oportunidade.objects.select_related(
        'lead', 'vendedor', 'lead__conta', 'empresa_prestadora'
    ).prefetch_related('atividades').all()
    serializer_class = OportunidadeSerializer
    pagination_class = CRMPagination

    vendedor_filter_field = 'vendedor_id'
    vendedor_filter_related = []
    cache_keys = ['oportunidades', 'dashboard']

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        db_name = get_current_tenant_db()
        if db_name and db_name != 'default':
            try:
                from django.db import connections

                conn = connections[db_name]
                with conn.cursor() as cur:
                    cur.execute(
                        'ALTER TABLE crm_vendas_atividade '
                        'ADD COLUMN IF NOT EXISTS conta_id BIGINT NULL;'
                    )
            except Exception:
                pass

    def _sanitize_vendedor_for_create(self, data):
        vendedor_id = data.get('vendedor')
        if vendedor_id is None:
            return data
        try:
            vid = int(vendedor_id) if not isinstance(vendedor_id, int) else vendedor_id
        except (TypeError, ValueError):
            data = data.copy()
            data.pop('vendedor', None)
            return data
        if not Vendedor.objects.filter(id=vid).exists():
            logger.warning(
                'Oportunidade create: vendedor_id=%s não existe no tenant, removendo do payload',
                vid,
            )
            data = data.copy()
            data.pop('vendedor', None)
        return data

    def create(self, request, *args, **kwargs):
        raw = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        data = self._sanitize_vendedor_for_create(raw)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def list(self, request, *args, **kwargs):
        return aplicar_cache_control_sem_store(super().list(request, *args, **kwargs))

    def perform_create(self, serializer):
        service = OportunidadeService(self.request)
        oportunidade = service.criar_oportunidade(serializer.validated_data)
        serializer.instance = oportunidade
        self._invalidate_caches()

    def perform_update(self, serializer):
        service = OportunidadeService(self.request)
        oportunidade = service.atualizar_oportunidade(
            serializer.instance, serializer.validated_data
        )
        serializer.instance = oportunidade
        self._invalidate_caches()

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related(
            'lead', 'vendedor', 'lead__conta', 'empresa_prestadora'
        ).prefetch_related(
            'atividades',
            'itens',
            'itens__produto_servico',
        )
        if get_current_vendedor_id(self.request) is None:
            qs = filtrar_queryset_por_query_params(qs, self.request, {'vendedor_id': 'vendedor_id'})
        return filtrar_queryset_por_query_params(qs, self.request, {'etapa': 'etapa'})


class AtividadeViewSet(CacheInvalidationMixin, VendedorFilterMixin, BaseModelViewSet):
    queryset = (
        Atividade.objects.select_related(
            'oportunidade',
            'lead',
            'oportunidade__vendedor',
            'lead__conta',
        )
        .defer('google_event_id')
        .all()
    )
    serializer_class = AtividadeListSerializer
    pagination_class = CRMPagination

    vendedor_filter_field = 'oportunidade__vendedor_id'
    vendedor_filter_related = ['lead__oportunidades__vendedor_id']
    cache_keys = ['atividades', 'dashboard']

    def _ensure_atividade_schema(self):
        db_name = get_current_tenant_db()
        if db_name and db_name != 'default':
            from .schema_service import patch_atividade_lembrete_columns_if_missing
            patch_atividade_lembrete_columns_if_missing(db_name)

    def dispatch(self, request, *args, **kwargs):
        try:
            self._ensure_atividade_schema()
        except Exception:
            logger.exception('Falha ao aplicar patch de lembrete em atividades')
        return super().dispatch(request, *args, **kwargs)

    def filter_by_vendedor(self, queryset):
        vendedor_id = get_current_vendedor_id(self.request)
        if vendedor_id is None:
            return queryset

        filters = (
            Q(oportunidade__vendedor_id=vendedor_id)
            | Q(lead__oportunidades__vendedor_id=vendedor_id)
            | Q(lead__vendedor_id=vendedor_id)
            | Q(
                oportunidade__isnull=True,
                lead__isnull=True,
                criado_por_vendedor_id=vendedor_id,
            )
        )
        return queryset.filter(filters).distinct()

    def perform_create(self, serializer):
        vendedor_id = get_current_vendedor_id(self.request)
        if vendedor_id is not None:
            serializer.save(criado_por_vendedor_id=vendedor_id)
        else:
            serializer.save()
        atividade = serializer.instance
        if atividade and getattr(atividade, 'loja_id', None):
            try:
                from superadmin.models import Loja
                from notificacoes.services import notify

                loja = (
                    Loja.objects.using('default')
                    .filter(id=atividade.loja_id)
                    .select_related('owner')
                    .first()
                )
                if loja and loja.owner_id:
                    data_str = (
                        atividade.data.strftime('%d/%m/%Y %H:%M') if atividade.data else ''
                    )
                    tipo_label = (
                        atividade.get_tipo_display()
                        if hasattr(atividade, 'get_tipo_display')
                        else atividade.tipo
                    )
                    notify(
                        user=loja.owner,
                        titulo=(
                            f'Nova atividade: {atividade.titulo[:50]}'
                            f'{"..." if len(atividade.titulo) > 50 else ""}'
                        ),
                        mensagem=f'{tipo_label}: {atividade.titulo} — {data_str}',
                        tipo='tarefa',
                        canal='in_app',
                        metadata={
                            'url': f'/loja/{loja.slug}/crm-vendas/calendario',
                            'atividade_id': atividade.id,
                            'loja_id': loja.id,
                        },
                    )
            except Exception:
                pass

            sync_atividade_create(self.request, atividade)
        self._disparar_lembretes_atividade(atividade)
        self._invalidate_caches()

    def _disparar_lembretes_atividade(self, atividade):
        loja_id = get_current_loja_id()
        if not loja_id or not atividade:
            return
        try:
            from .atividade_lembrete_service import tentar_lembretes_imediatos
            tentar_lembretes_imediatos(loja_id, atividade)
        except Exception:
            logger.exception('Falha ao disparar lembretes imediatos atividade %s', atividade.pk)

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return AtividadeSerializer
        return AtividadeListSerializer

    @cache_list_response(
        CRMCacheManager.ATIVIDADES,
        ttl=30,
        extra_keys=['data_inicio', 'data_fim', 'concluido'],
    )
    def list(self, request, *args, **kwargs):
        self._ensure_atividade_schema()
        return aplicar_cache_control_sem_store(super().list(request, *args, **kwargs))

    @action(detail=True, methods=['post'], url_path='enviar-whatsapp')
    def enviar_whatsapp(self, request, pk=None):
        atividade = self.get_object()
        loja_id = get_current_loja_id()
        if not loja_id:
            return Response({'error': 'Contexto de loja não encontrado.'}, status=status.HTTP_400_BAD_REQUEST)
        telefone = (request.data.get('telefone') or '').strip()
        from core.task_queue import task_queue_enabled

        ok, result = enviar_atividade_whatsapp(
            loja_id,
            atividade,
            telefone,
            user=getattr(request, 'user', None),
        )
        if not ok:
            return Response({'error': result}, status=status.HTTP_400_BAD_REQUEST)
        if task_queue_enabled():
            return Response({
                'success': True,
                'queued': True,
                'message': f'WhatsApp enfileirado para {result}.',
            })
        return Response({
            'success': True,
            'message': f'Lembrete enviado por WhatsApp para {result}',
        })

    def perform_update(self, serializer):
        super().perform_update(serializer)
        atividade = serializer.instance
        if atividade and getattr(atividade, 'loja_id', None):
            sync_atividade_update(self.request, atividade)
            self._disparar_lembretes_atividade(atividade)

    def perform_destroy(self, instance):
        try:
            from notificacoes.models import Notification
            from superadmin.models import Loja

            loja_id = get_current_loja_id()
            loja = (
                Loja.objects.using('default')
                .filter(id=loja_id)
                .select_related('owner')
                .first()
            )
            if loja and loja.owner_id:
                Notification.objects.filter(
                    user=loja.owner,
                    metadata__atividade_id=instance.id,
                ).delete()
                logger.info('Notificações da atividade %s removidas', instance.id)
        except Exception as e:
            logger.warning('Erro ao remover notificações da atividade: %s', e)

        if instance.google_event_id:
            sync_atividade_delete(get_current_loja_id(), instance)

        super().perform_destroy(instance)

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related('oportunidade', 'lead').defer('google_event_id')
        concluido = self.request.query_params.get('concluido')
        if concluido is not None:
            qs = qs.filter(concluido=concluido.lower() == 'true')
        qs = filtrar_queryset_por_query_params(
            qs,
            self.request,
            {'oportunidade_id': 'oportunidade_id', 'lead_id': 'lead_id'},
        )
        data_inicio = self.request.query_params.get('data_inicio')
        if data_inicio:
            dt = parse_datetime(data_inicio)
            if dt and timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.utc)
            if dt:
                qs = qs.filter(data__gte=dt)
        data_fim = self.request.query_params.get('data_fim')
        if data_fim:
            dt = parse_datetime(data_fim)
            if dt and timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.utc)
            if dt:
                qs = qs.filter(data__lte=dt)
        return qs
