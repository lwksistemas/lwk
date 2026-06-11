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

    def _iniciar_assinatura_cliente(self, doc, loja_id, request, canal='email'):
        from .assinatura_digital_service import (
            criar_token_assinatura,
            enviar_email_assinatura_cliente,
            enviar_whatsapp_assinatura_cliente,
        )

        label = self.assinatura_doc_label
        lead = doc.oportunidade.lead
        canal = (canal or 'email').strip().lower()
        if canal not in ('email', 'whatsapp'):
            return None, Response({'detail': 'Informe o canal: email ou whatsapp.'}, status=status.HTTP_400_BAD_REQUEST)

        if canal == 'email':
            if not lead.email:
                return None, Response(
                    {'detail': 'Lead não possui email cadastrado.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        elif not (getattr(lead, 'telefone', None) or '').strip():
            return None, Response(
                {'detail': 'Lead não possui telefone cadastrado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        assinatura = criar_token_assinatura(doc, 'cliente', loja_id)
        doc.status_assinatura = 'aguardando_cliente'
        update_fields = ['status_assinatura', 'updated_at']
        if hasattr(doc, 'status') and doc.status == 'rascunho':
            doc.status = 'enviada'
            update_fields.append('status')
        doc.save(update_fields=update_fields)

        if canal == 'whatsapp':
            ok, err = enviar_whatsapp_assinatura_cliente(
                doc, assinatura, request, user=request.user,
            )
            destino = (lead.telefone or '').strip()
            msg_ok = f'Link de assinatura enviado por WhatsApp para {destino}'
        else:
            ok, err = enviar_email_assinatura_cliente(doc, assinatura, request)
            msg_ok = f'Email de assinatura enviado para {lead.email}'

        if ok:
            if self.assinatura_cache_key:
                from .cache import CRMCacheManager
                CRMCacheManager.invalidate(self.assinatura_cache_key, loja_id)
            return assinatura, Response({
                'message': msg_ok,
                'status_assinatura': 'aguardando_cliente',
                'canal': canal,
            })

        doc.status_assinatura = 'rascunho'
        doc.save(update_fields=['status_assinatura', 'updated_at'])
        assinatura.delete()
        return None, Response(
            {'detail': err or f'Erro ao enviar {canal}. Tente novamente.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    @action(detail=True, methods=['post'])
    def enviar_para_assinatura(self, request, pk=None):
        """Inicia workflow de assinatura digital. Envia e-mail ou WhatsApp para o cliente."""
        doc = self.get_object()
        loja_id = get_current_loja_id()
        label = self.assinatura_doc_label

        if not doc.oportunidade or not doc.oportunidade.lead:
            return Response(
                {'detail': f'{label} sem oportunidade ou lead vinculado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if doc.status_assinatura in ['aguardando_cliente', 'aguardando_vendedor']:
            return Response(
                {'detail': f'{label} já está em processo de assinatura: {doc.get_status_assinatura_display()}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        canal = (request.data.get('canal') or 'email').strip().lower()
        canal_vendedor = (request.data.get('canal_vendedor') or 'email').strip().lower()
        if canal_vendedor not in ('email', 'whatsapp'):
            return Response(
                {'detail': 'Informe canal_vendedor: email ou whatsapp.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if canal_vendedor == 'whatsapp':
            from .assinatura_digital_service import _telefone_vendedor_documento
            if not _telefone_vendedor_documento(doc):
                return Response(
                    {'detail': 'Vendedor não possui telefone cadastrado para assinatura por WhatsApp.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        doc.canal_assinatura_vendedor = canal_vendedor
        doc.save(update_fields=['canal_assinatura_vendedor', 'updated_at'])

        _, response = self._iniciar_assinatura_cliente(doc, loja_id, request, canal=canal)
        return response

    @action(detail=True, methods=['post'])
    def reenviar_para_assinatura(self, request, pk=None):
        """Reenvia link de assinatura (e-mail ou WhatsApp para cliente; e-mail para vendedor)."""
        from .assinatura_digital_service import reenviar_link_assinatura_pendente

        doc = self.get_object()
        loja_id = get_current_loja_id()
        label = self.assinatura_doc_label

        if not doc.oportunidade or not doc.oportunidade.lead:
            return Response(
                {'detail': f'{label} sem oportunidade ou lead vinculado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        canal = (request.data.get('canal') or 'email').strip().lower()
        ok, msg, err = reenviar_link_assinatura_pendente(doc, loja_id, request, canal=canal)
        if ok:
            if self.assinatura_cache_key:
                from .cache import CRMCacheManager
                CRMCacheManager.invalidate(self.assinatura_cache_key, loja_id)
            return Response({
                'message': msg,
                'status_assinatura': doc.status_assinatura,
                'canal': canal,
            })
        if err and err.startswith('Reenvio só é possível'):
            return Response({'detail': err}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {'detail': err or 'Erro ao reenviar.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
