"""
Mixin para workflow de assinatura digital (Proposta e Contrato).
Elimina duplicação entre PropostaViewSet e ContratoViewSet (refatoração #1 — DRY).
"""
import logging

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from tenants.middleware import get_current_loja_id
from .decorators import invalidate_cache_on_change

logger = logging.getLogger(__name__)


class AssinaturaDigitalMixin:
    """
    Mixin que adiciona enviar_para_assinatura e reenviar_para_assinatura.
    
    Requer:
        - self.get_object() retorna Proposta ou Contrato
        - O model tem: oportunidade, status_assinatura, get_status_assinatura_display()
    
    Configuração:
        assinatura_doc_label: 'Proposta' ou 'Contrato' (para mensagens)
        assinatura_cache_key: chave de cache para invalidar (ex: 'propostas')
    """
    assinatura_doc_label = 'Documento'
    assinatura_cache_key = None

    @action(detail=True, methods=['post'])
    def enviar_para_assinatura(self, request, pk=None):
        """Inicia workflow de assinatura digital. Envia email para cliente."""
        from .assinatura_digital_service import criar_token_assinatura, enviar_email_assinatura_cliente

        doc = self.get_object()
        loja_id = get_current_loja_id()
        label = self.assinatura_doc_label

        if not doc.oportunidade or not doc.oportunidade.lead:
            return Response(
                {'detail': f'{label} sem oportunidade ou lead vinculado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        lead = doc.oportunidade.lead
        if not lead.email:
            return Response(
                {'detail': 'Lead não possui email cadastrado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if doc.status_assinatura in ['aguardando_cliente', 'aguardando_vendedor']:
            return Response(
                {'detail': f'{label} já está em processo de assinatura: {doc.get_status_assinatura_display()}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        assinatura = criar_token_assinatura(doc, 'cliente', loja_id)
        doc.status_assinatura = 'aguardando_cliente'
        doc.save(update_fields=['status_assinatura', 'updated_at'])

        ok, err = enviar_email_assinatura_cliente(doc, assinatura, request)
        if ok:
            # Invalidar cache se configurado
            if self.assinatura_cache_key:
                from .cache import CRMCacheManager
                CRMCacheManager.invalidate(self.assinatura_cache_key, loja_id)
            return Response({
                'message': f'Email de assinatura enviado para {lead.email}',
                'status_assinatura': 'aguardando_cliente',
            })

        # Reverter se falhou
        doc.status_assinatura = 'rascunho'
        doc.save(update_fields=['status_assinatura', 'updated_at'])
        assinatura.delete()
        return Response(
            {'detail': err or 'Erro ao enviar email. Tente novamente.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    @action(detail=True, methods=['post'])
    def reenviar_para_assinatura(self, request, pk=None):
        """Reenvia e-mail com link de assinatura (novo token)."""
        from .assinatura_digital_service import reenviar_link_assinatura_pendente

        doc = self.get_object()
        loja_id = get_current_loja_id()
        label = self.assinatura_doc_label

        if not doc.oportunidade or not doc.oportunidade.lead:
            return Response(
                {'detail': f'{label} sem oportunidade ou lead vinculado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ok, msg, err = reenviar_link_assinatura_pendente(doc, loja_id, request)
        if ok:
            if self.assinatura_cache_key:
                from .cache import CRMCacheManager
                CRMCacheManager.invalidate(self.assinatura_cache_key, loja_id)
            return Response({
                'message': msg,
                'status_assinatura': doc.status_assinatura,
            })
        if err and err.startswith('Reenvio só é possível'):
            return Response({'detail': err}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {'detail': err or 'Erro ao reenviar.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
