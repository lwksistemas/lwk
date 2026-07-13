"""ViewSets de pipeline: oportunidades e atividades."""
import logging

from django.db.models import Case, DateField, Q, When
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.views import BaseModelViewSet
from tenants.middleware import get_current_loja_id

from .activities_google_sync_queue import (
    dispatch_sync_atividade_delete,
    dispatch_sync_atividade_update,
)
from .atividade_whatsapp_service import enviar_atividade_whatsapp
from .cache import CRMCacheManager
from .decorators import cache_list_response
from .mixins import (
    CacheInvalidationMixin,
    CrmGranularPermissionMixin,
    CRMSchemaRecoveryMixin,
    VendedorFilterMixin,
)
from .models import Atividade, Oportunidade, OportunidadeNota, Vendedor
from .serializers import (
    AtividadeListSerializer,
    AtividadeSerializer,
    OportunidadeNotaSerializer,
    OportunidadeSerializer,
)
from .services import OportunidadeService
from .utils import get_current_vendedor_id
from .views_common import CRMPagination, aplicar_cache_control_sem_store, filtrar_queryset_por_query_params

logger = logging.getLogger(__name__)


def _filtrar_oportunidades_por_periodo(qs, data_inicio_str, data_fim_str):
    """Filtra por data de referência: abertas → created_at;
    ganho → data_fechamento_ganho/data_fechamento; perdido → data_fechamento_perdido.
    """
    di = parse_date(data_inicio_str) if data_inicio_str else None
    df = parse_date(data_fim_str) if data_fim_str else None
    if not di and not df:
        return qs

    created_date = TruncDate("created_at")
    qs = qs.annotate(
        data_ref_periodo=Case(
            When(
                etapa="closed_won",
                then=Coalesce("data_fechamento_ganho", "data_fechamento", created_date),
            ),
            When(
                etapa="closed_lost",
                then=Coalesce("data_fechamento_perdido", created_date),
            ),
            default=created_date,
            output_field=DateField(),
        ),
    )
    if di:
        qs = qs.filter(data_ref_periodo__gte=di)
    if df:
        qs = qs.filter(data_ref_periodo__lte=df)
    return qs


class OportunidadeViewSet(
    CRMSchemaRecoveryMixin,
    CrmGranularPermissionMixin,
    CacheInvalidationMixin,
    VendedorFilterMixin,
    BaseModelViewSet,
):
    queryset = Oportunidade.objects.select_related(
        "lead", "vendedor", "lead__conta", "empresa_prestadora",
    ).all()
    serializer_class = OportunidadeSerializer
    pagination_class = CRMPagination

    vendedor_filter_field = "vendedor_id"
    vendedor_filter_related = []
    cache_keys = ["oportunidades", "dashboard"]
    crm_permission_model = "oportunidade"

    def _sanitize_vendedor_for_create(self, data):
        vendedor_id = data.get("vendedor")
        if vendedor_id is None:
            return data
        try:
            vid = int(vendedor_id) if not isinstance(vendedor_id, int) else vendedor_id
        except (TypeError, ValueError):
            data = data.copy()
            data.pop("vendedor", None)
            return data
        if not Vendedor.objects.filter(id=vid).exists():
            logger.warning(
                "Oportunidade create: vendedor_id=%s não existe no tenant, removendo do payload",
                vid,
            )
            data = data.copy()
            data.pop("vendedor", None)
        return data

    def create(self, request, *args, **kwargs):
        raw = request.data.copy() if hasattr(request.data, "copy") else dict(request.data)
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
            serializer.instance, serializer.validated_data,
        )
        serializer.instance = oportunidade
        self._invalidate_caches()

    def get_queryset(self):
        qs = Oportunidade.objects.select_related(
            "lead", "vendedor", "lead__conta", "empresa_prestadora",
        )
        # Listagem do pipeline não precisa de atividades/itens (serializer de lista não usa)
        if getattr(self, "action", None) != "list":
            qs = qs.prefetch_related(
                "atividades",
                "itens",
                "itens__produto_servico",
            )
        if get_current_vendedor_id(self.request) is None:
            qs = filtrar_queryset_por_query_params(qs, self.request, {"vendedor_id": "vendedor_id"})
        qs = filtrar_queryset_por_query_params(qs, self.request, {"etapa": "etapa"})
        return _filtrar_oportunidades_por_periodo(
            qs,
            self.request.query_params.get("data_inicio"),
            self.request.query_params.get("data_fim"),
        )


def _autor_nome_negociacao(request) -> str:
    vid = get_current_vendedor_id(request)
    if vid:
        vendedor = Vendedor.objects.filter(id=vid).only("nome").first()
        if vendedor and vendedor.nome:
            return vendedor.nome
    user = getattr(request, "user", None)
    if user and user.is_authenticated:
        nome = (user.get_full_name() or "").strip() or getattr(user, "username", "")
        if nome:
            return nome
    return "Equipe"


class OportunidadeNotaViewSet(
    CRMSchemaRecoveryMixin,
    CrmGranularPermissionMixin,
    CacheInvalidationMixin,
    VendedorFilterMixin,
    BaseModelViewSet,
):
    """Notas cronológicas da negociação (respostas do cliente e notas internas).

    Design intencional: append-only (sem PUT/PATCH/DELETE).
    O histórico de negociação é imutável — notas não podem ser editadas ou removidas,
    apenas adicionadas. Isso garante rastreabilidade completa da conversa com o cliente.
    """

    queryset = OportunidadeNota.objects.select_related("oportunidade").all()
    serializer_class = OportunidadeNotaSerializer
    pagination_class = CRMPagination
    http_method_names = ["get", "post", "head", "options"]

    vendedor_filter_field = "oportunidade__vendedor_id"
    vendedor_filter_related = []
    cache_keys = ["oportunidades"]
    crm_permission_model = "oportunidade"

    def get_queryset(self):
        qs = super().get_queryset()
        return filtrar_queryset_por_query_params(
            qs,
            self.request,
            {"oportunidade_id": "oportunidade_id"},
        )

    def perform_create(self, serializer):
        serializer.save(autor_nome=_autor_nome_negociacao(self.request))
        self._invalidate_caches()


class AtividadeViewSet(
    CRMSchemaRecoveryMixin,
    CrmGranularPermissionMixin,
    CacheInvalidationMixin,
    VendedorFilterMixin,
    BaseModelViewSet,
):
    queryset = (
        Atividade.objects.select_related(
            "oportunidade",
            "lead",
            "oportunidade__vendedor",
            "lead__conta",
        )
        .defer("google_event_id")
        .all()
    )
    serializer_class = AtividadeListSerializer
    pagination_class = CRMPagination

    vendedor_filter_field = "oportunidade__vendedor_id"
    vendedor_filter_related = ["lead__oportunidades__vendedor_id"]
    cache_keys = ["atividades", "dashboard"]
    crm_permission_model = "atividade"

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
        if atividade and getattr(atividade, "loja_id", None):
            try:
                from notificacoes.services import notify
                from superadmin.models import Loja

                loja = (
                    Loja.objects.using("default")
                    .filter(id=atividade.loja_id)
                    .select_related("owner")
                    .first()
                )
                if loja and loja.owner_id:
                    data_str = (
                        atividade.data.strftime("%d/%m/%Y %H:%M") if atividade.data else ""
                    )
                    tipo_label = (
                        atividade.get_tipo_display()
                        if hasattr(atividade, "get_tipo_display")
                        else atividade.tipo
                    )
                    notify(
                        user=loja.owner,
                        titulo=(
                            f'Nova atividade: {atividade.titulo[:50]}'
                            f'{"..." if len(atividade.titulo) > 50 else ""}'
                        ),
                        mensagem=f"{tipo_label}: {atividade.titulo} — {data_str}",
                        tipo="tarefa",
                        canal="in_app",
                        metadata={
                            "url": f"/loja/{loja.slug}/crm-vendas/calendario",
                            "atividade_id": atividade.id,
                            "loja_id": loja.id,
                        },
                    )
            except Exception as e:
                logger.warning(
                    "Falha ao enviar notificação in-app de atividade=%s loja_id=%s: %s",
                    atividade.id, atividade.loja_id, e,
                )
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
            logger.exception("Falha ao disparar lembretes imediatos atividade %s", atividade.pk)

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return AtividadeSerializer
        return AtividadeListSerializer

    @cache_list_response(
        CRMCacheManager.ATIVIDADES,
        ttl=30,
        extra_keys=["data_inicio", "data_fim", "concluido"],
    )
    def list(self, request, *args, **kwargs):
        return aplicar_cache_control_sem_store(super().list(request, *args, **kwargs))

    @action(detail=True, methods=["post"], url_path="enviar-whatsapp")
    def enviar_whatsapp(self, request, pk=None):
        atividade = self.get_object()
        loja_id = get_current_loja_id()
        if not loja_id:
            return Response({"error": "Contexto de loja não encontrado."}, status=status.HTTP_400_BAD_REQUEST)
        telefone = (request.data.get("telefone") or "").strip()
        from core.task_queue import task_queue_enabled

        ok, result = enviar_atividade_whatsapp(
            loja_id,
            atividade,
            telefone,
            user=getattr(request, "user", None),
        )
        if not ok:
            return Response({"error": result}, status=status.HTTP_400_BAD_REQUEST)
        if task_queue_enabled():
            return Response({
                "success": True,
                "queued": True,
                "message": f"WhatsApp enfileirado para {result}.",
            })
        return Response({
            "success": True,
            "message": f"Lembrete enviado por WhatsApp para {result}",
        })

    def perform_update(self, serializer):
        super().perform_update(serializer)
        atividade = serializer.instance
        if atividade and getattr(atividade, "loja_id", None):
            dispatch_sync_atividade_update(self.request, atividade)
            self._disparar_lembretes_atividade(atividade)

    def perform_destroy(self, instance):
        try:
            from notificacoes.models import Notification
            from superadmin.models import Loja

            loja_id = get_current_loja_id()
            loja = (
                Loja.objects.using("default")
                .filter(id=loja_id)
                .select_related("owner")
                .first()
            )
            if loja and loja.owner_id:
                Notification.objects.filter(
                    user=loja.owner,
                    metadata__atividade_id=instance.id,
                ).delete()
                logger.info("Notificações da atividade %s removidas", instance.id)
        except Exception as e:
            logger.warning("Erro ao remover notificações da atividade: %s", e)

        if instance.google_event_id:
            dispatch_sync_atividade_delete(self.request, instance, loja_id=get_current_loja_id())

        super().perform_destroy(instance)

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related("oportunidade", "lead").defer("google_event_id")
        concluido = self.request.query_params.get("concluido")
        if concluido is not None:
            qs = qs.filter(concluido=concluido.lower() == "true")
        qs = filtrar_queryset_por_query_params(
            qs,
            self.request,
            {"oportunidade_id": "oportunidade_id", "lead_id": "lead_id"},
        )
        data_inicio = self.request.query_params.get("data_inicio")
        if data_inicio:
            dt = parse_datetime(data_inicio)
            if dt and timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.utc)
            if dt:
                qs = qs.filter(data__gte=dt)
        data_fim = self.request.query_params.get("data_fim")
        if data_fim:
            dt = parse_datetime(data_fim)
            if dt and timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.utc)
            if dt:
                qs = qs.filter(data__lte=dt)
        return qs
