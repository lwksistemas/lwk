"""ViewSets financeiro CRM — receitas/despesas por vendedor."""
import logging

from rest_framework import status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import HttpResponse

from core.views import BaseModelViewSet
from tenants.middleware import get_current_loja_id

from .mixins import (
    CRMPermissionMixin,
    CacheInvalidationMixin,
    CRMSchemaRecoveryMixin,
    VendedorFilterMixin,
)
from .models.financeiro import GrupoFinanceiroCRM, LancamentoFinanceiroCRM
from .serializers.financeiro import (
    GrupoFinanceiroCRMSerializer,
    LancamentoFinanceiroCRMSerializer,
)
from .services_financeiro import (
    garantir_grupos_padrao,
    resumo_financeiro_crm,
    sincronizar_comissoes_retroativas,
)
from .utils import get_current_vendedor_id, is_owner
from .views_common import CRMPagination, filtrar_queryset_por_query_params

logger = logging.getLogger(__name__)


class GrupoFinanceiroCRMViewSet(
    CRMSchemaRecoveryMixin,
    CRMPermissionMixin,
    CacheInvalidationMixin,
    BaseModelViewSet,
):
    queryset = GrupoFinanceiroCRM.objects.all()
    serializer_class = GrupoFinanceiroCRMSerializer
    pagination_class = CRMPagination
    cache_keys = ['financeiro_crm']

    def get_queryset(self):
        loja_id = get_current_loja_id()
        if loja_id:
            garantir_grupos_padrao(loja_id)
        qs = super().get_queryset()
        return filtrar_queryset_por_query_params(qs, self.request, {'tipo': 'tipo'})

    def create(self, request, *args, **kwargs):
        bloqueio = self.bloquear_vendedor(request, 'Apenas o administrador pode criar grupos.')
        if bloqueio:
            return bloqueio
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        bloqueio = self.bloquear_vendedor(request, 'Apenas o administrador pode editar grupos.')
        if bloqueio:
            return bloqueio
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        bloqueio = self.bloquear_vendedor(request, 'Apenas o administrador pode excluir grupos.')
        if bloqueio:
            return bloqueio
        inst = self.get_object()
        if inst.lancamentos.exists():
            return Response(
                {'detail': 'Grupo em uso. Desative-o ou mova os lançamentos antes de excluir.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)


class LancamentoFinanceiroCRMViewSet(
    CRMSchemaRecoveryMixin,
    CacheInvalidationMixin,
    VendedorFilterMixin,
    BaseModelViewSet,
):
    queryset = LancamentoFinanceiroCRM.objects.select_related(
        'vendedor', 'grupo', 'oportunidade'
    ).all()
    serializer_class = LancamentoFinanceiroCRMSerializer
    pagination_class = CRMPagination
    vendedor_filter_field = 'vendedor_id'
    cache_keys = ['financeiro_crm', 'dashboard']

    def get_queryset(self):
        qs = super().get_queryset()
        return filtrar_queryset_por_query_params(
            qs,
            self.request,
            {
                'tipo': 'tipo',
                'status': 'status',
                'vendedor_id': 'vendedor_id',
                'grupo_id': 'grupo_id',
            },
        )

    def perform_create(self, serializer):
        vendedor_id = get_current_vendedor_id(self.request)
        if vendedor_id and not is_owner(self.request):
            serializer.save(
                vendedor_id=vendedor_id,
                origem=LancamentoFinanceiroCRM.ORIGEM_MANUAL,
            )
        else:
            serializer.save(origem=LancamentoFinanceiroCRM.ORIGEM_MANUAL)
        self._invalidate_caches()

    def perform_update(self, serializer):
        inst = serializer.instance
        if inst.origem == LancamentoFinanceiroCRM.ORIGEM_COMISSAO:
            allowed = {'status', 'data_pagamento', 'observacoes', 'grupo'}
            data = {k: v for k, v in serializer.validated_data.items() if k in allowed}
            for k, v in data.items():
                setattr(inst, k, v)
            inst.save()
            serializer.instance = inst
        else:
            super().perform_update(serializer)
        self._invalidate_caches()

    def destroy(self, request, *args, **kwargs):
        inst = self.get_object()
        if inst.origem == LancamentoFinanceiroCRM.ORIGEM_COMISSAO:
            return Response(
                {'detail': 'Receitas de comissão automática não podem ser excluídas. Cancele na oportunidade.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def marcar_pago(self, request, pk=None):
        from django.utils import timezone

        inst = self.get_object()
        inst.status = LancamentoFinanceiroCRM.STATUS_PAGO
        inst.data_pagamento = request.data.get('data_pagamento') or timezone.now().date()
        inst.save(update_fields=['status', 'data_pagamento', 'updated_at'])
        self._invalidate_caches()
        return Response(self.get_serializer(inst).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def financeiro_crm_resumo(request):
    from django.db.utils import OperationalError, ProgrammingError
    from superadmin.models import Loja

    from .schema_service import configurar_schema_crm_loja

    loja_id = get_current_loja_id()
    if not loja_id:
        return Response({'error': 'Loja não identificada'}, status=status.HTTP_400_BAD_REQUEST)

    vendedor_id = get_current_vendedor_id(request)
    filtro = request.query_params.get('vendedor_id')
    if is_owner(request) and filtro:
        try:
            vendedor_id = int(filtro)
        except (TypeError, ValueError):
            pass
    elif not is_owner(request):
        vendedor_id = vendedor_id

    for attempt in range(2):
        try:
            garantir_grupos_padrao(loja_id)
            return Response(resumo_financeiro_crm(loja_id, vendedor_id))
        except (ProgrammingError, OperationalError):
            if attempt == 0:
                loja = Loja.objects.filter(id=loja_id).select_related('tipo_loja').first()
                if loja and configurar_schema_crm_loja(loja):
                    continue
            logger.exception('Erro no resumo financeiro CRM (loja_id=%s)', loja_id)
            return Response(
                {'detail': 'O banco de dados da loja precisa ser configurado.', 'code': 'SCHEMA_NOT_CONFIGURED'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def financeiro_crm_relatorio_pdf(request):
    """Gera PDF do financeiro por vendedor/grupo no período."""
    loja_id = get_current_loja_id()
    if not loja_id:
        return Response({'detail': 'Loja não identificada.'}, status=status.HTTP_400_BAD_REQUEST)

    periodo = request.data.get('periodo', 'mes_atual')
    data_inicio = request.data.get('data_inicio')
    data_fim = request.data.get('data_fim')
    grupo_id = request.data.get('grupo_id')
    vendedor_id = request.data.get('vendedor_id')

    current_vendedor_id = get_current_vendedor_id(request)
    if current_vendedor_id and not is_owner(request):
        vendedor_id = current_vendedor_id
    elif vendedor_id:
        try:
            vendedor_id = int(vendedor_id)
        except (TypeError, ValueError):
            vendedor_id = None

    if grupo_id:
        try:
            grupo_id = int(grupo_id)
        except (TypeError, ValueError):
            grupo_id = None

    if periodo == 'personalizado' and (not data_inicio or not data_fim):
        return Response(
            {'detail': 'Informe data_inicio e data_fim para período personalizado.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        from .relatorios_financeiro import gerar_relatorio_financeiro_vendedor

        pdf_buffer = gerar_relatorio_financeiro_vendedor(
            loja_id,
            periodo=periodo,
            vendedor_id=vendedor_id,
            grupo_id=grupo_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="financeiro_crm_{periodo}.pdf"'
        return response
    except Exception as exc:
        logger.exception('Erro ao gerar PDF financeiro CRM: %s', exc)
        return Response({'detail': 'Erro ao gerar relatório PDF.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def financeiro_crm_sync_comissoes(request):
    """Sincroniza receitas de comissão a partir de oportunidades já ganhas."""
    loja_id = get_current_loja_id()
    if not loja_id:
        return Response({'detail': 'Loja não identificada.'}, status=status.HTTP_400_BAD_REQUEST)

    if not is_owner(request):
        return Response(
            {'detail': 'Apenas o administrador pode sincronizar comissões retroativas.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    dry_run = bool(request.data.get('dry_run', False))
    result = sincronizar_comissoes_retroativas(loja_id, dry_run=dry_run)
    return Response({'success': True, **result})
