"""
Mixins para eliminar duplicação entre Proposta/Contrato ViewSets e Template ViewSets.
Refatoração #2 e #3 — DRY.
"""
import logging

from rest_framework.decorators import action
from rest_framework.response import Response

from tenants.middleware import get_current_loja_id, ensure_loja_context
from .views_common import filtrar_queryset_por_query_params

logger = logging.getLogger(__name__)


class DocumentoQuerysetMixin:
    """
    Mixin para get_queryset de PropostaViewSet e ContratoViewSet.
    Ambos filtram por oportunidade_id e status, com os mesmos select_related.
    
    Requer:
        - documento_select_related: tuple de campos para select_related
    """
    documento_select_related = (
        'oportunidade',
        'oportunidade__lead',
        'oportunidade__lead__conta',
        'oportunidade__vendedor',
    )
    documento_prefetch_related = ('oportunidade__itens__produto_servico',)

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related(*self.documento_select_related).prefetch_related(
            *self.documento_prefetch_related
        )
        qs = filtrar_queryset_por_query_params(
            qs,
            self.request,
            {'oportunidade_id': 'oportunidade_id'},
        )
        status = self.request.query_params.get('status')
        if status == 'pedido':
            # Aba "Concluída" no CRM: aceita (assinada) + pedido (confirmado).
            qs = qs.filter(status__in=['aceita', 'pedido'])
        elif status:
            qs = qs.filter(status=status)
        return qs


class TemplateViewSetMixin:
    """
    Mixin para PropostaTemplateViewSet e ContratoTemplateViewSet.
    Elimina get_queryset e marcar_padrao duplicados.
    
    Requer:
        - template_model: classe do model (PropostaTemplate ou ContratoTemplate)
    """
    template_model = None

    def get_queryset(self):
        if hasattr(self, 'request') and self.request:
            ensure_loja_context(self.request)
        loja_id = get_current_loja_id()

        if not loja_id:
            logger.warning(f"[{self.__class__.__name__}] Acesso sem loja_id no contexto")
            return self.template_model.objects.none()

        qs = self.template_model.objects.filter(loja_id=loja_id)

        ativo = self.request.query_params.get('ativo')
        if ativo is None or ativo.lower() == 'true':
            qs = qs.filter(ativo=True)
        elif ativo.lower() == 'false':
            qs = qs.filter(ativo=False)

        return qs

    @action(detail=True, methods=['post'])
    def marcar_padrao(self, request, pk=None):
        """Marca este template como padrão (desmarca outros)."""
        template = self.get_object()
        template.is_padrao = True
        template.save()
        return Response({'message': 'Template marcado como padrão.'})
