"""
CRM: WhatsApp e personalização da tela de login.
"""
import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from whatsapp.config_helpers import apply_whatsapp_config_patch, serialize_whatsapp_config
from whatsapp.views_connection import (
    WhatsAppConnectView as BaseWhatsAppConnectView,
    WhatsAppConnectionStatusView as BaseWhatsAppConnectionStatusView,
    WhatsAppDisconnectView as BaseWhatsAppDisconnectView,
)
from .mixins import CRMPermissionMixin
from .decorators import require_admin_access
from .utils import get_loja_from_context

logger = logging.getLogger(__name__)

class WhatsAppConfigView(CRMPermissionMixin, APIView):
    """
    Configuração WhatsApp da loja (reutiliza WhatsAppConfig da Clínica da Beleza).
    GET /crm-vendas/whatsapp-config/  → retorna flags
    PATCH /crm-vendas/whatsapp-config/ → atualiza flags
    """
    permission_classes = [IsAuthenticated]

    def _get_config(self, request=None):
        loja = get_loja_from_context(request)
        if not loja:
            logger.warning("WhatsAppConfigView: contexto de loja não encontrado")
            return None
        
        from whatsapp.models import WhatsAppConfig
        try:
            owner_tel = (getattr(loja, 'owner_telefone', None) or '').strip()
            config, created = WhatsAppConfig.objects.get_or_create(
                loja=loja,
                defaults={
                    'enviar_confirmacao': True,
                    'enviar_lembrete_24h': True,
                    'enviar_lembrete_2h': True,
                    'enviar_cobranca': True,
                    'enviar_lembrete_tarefas': True,
                    'whatsapp_numero': owner_tel or '',
                }
            )
            if not created and not (config.whatsapp_numero or '').strip() and owner_tel:
                config.whatsapp_numero = owner_tel
                config.save(update_fields=['whatsapp_numero', 'updated_at'])
            return config
        except Exception as e:
            logger.exception("WhatsAppConfigView._get_config erro: %s", e)
            return None

    def _serialize_config(self, config, *, sync_evolution=False):
        return serialize_whatsapp_config(config, loja=config.loja, sync_evolution=sync_evolution)

    @require_admin_access()
    def get(self, request):
        config = self._get_config(request)
        if config is None:
            return Response(
                {'error': 'Contexto de loja não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(self._serialize_config(config, sync_evolution=True))

    @require_admin_access()
    def patch(self, request):
        config = self._get_config(request)
        if config is None:
            return Response(
                {'error': 'Contexto de loja não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        update_fields, err = apply_whatsapp_config_patch(config, request.data)
        if err:
            return err
        config.save(update_fields=update_fields)
        return Response(self._serialize_config(config))


class CRMWhatsAppConnectionStatusView(CRMPermissionMixin, BaseWhatsAppConnectionStatusView):
    permission_classes = [IsAuthenticated]

    @require_admin_access()
    def get(self, request):
        return super().get(request)

    def _get_config(self, request):
        return WhatsAppConfigView()._get_config(request)


class CRMWhatsAppConnectView(CRMPermissionMixin, BaseWhatsAppConnectView):
    permission_classes = [IsAuthenticated]

    @require_admin_access()
    def post(self, request):
        return super().post(request)

    def _get_config(self, request):
        return WhatsAppConfigView()._get_config(request)


class CRMWhatsAppDisconnectView(CRMPermissionMixin, BaseWhatsAppDisconnectView):
    permission_classes = [IsAuthenticated]

    @require_admin_access()
    def post(self, request):
        return super().post(request)

    def _get_config(self, request):
        return WhatsAppConfigView()._get_config(request)


class LoginConfigView(CRMPermissionMixin, APIView):
    """
    GET /crm-vendas/login-config/  → retorna logo, cor_primaria, cor_secundaria
    PATCH /crm-vendas/login-config/ → atualiza personalização da tela de login
    """
    permission_classes = [IsAuthenticated]

    @require_admin_access()
    def get(self, request):
        loja = get_loja_from_context(request)
        if loja is None:
            return Response(
                {'error': 'Contexto de loja não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        tipo = getattr(loja, 'tipo_loja', None)
        cor_default = getattr(tipo, 'cor_primaria', None) if tipo else None
        cor_primaria = (loja.cor_primaria or '').strip() or cor_default or '#10B981'
        cor_secundaria = (loja.cor_secundaria or '').strip() or '#059669'
        return Response({
            'logo': (loja.logo or '').strip(),
            'login_background': (loja.login_background or '').strip(),
            'login_logo': (loja.login_logo or '').strip(),
            'cor_primaria': cor_primaria,
            'cor_secundaria': cor_secundaria,
        })

    @require_admin_access()
    def patch(self, request):
        loja = get_loja_from_context(request)
        if loja is None:
            return Response(
                {'error': 'Contexto de loja não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Importar função de deleção do Cloudinary
        from superadmin.cloudinary_utils import delete_cloudinary_image
        
        update_fields = ['updated_at']
        loja_slug = loja.slug  # Slug da loja para validação de propriedade
        
        # Processar logo
        if 'logo' in request.data:
            val = (request.data.get('logo') or '').strip()
            old_logo = (loja.logo or '').strip()
            
            # Se mudou e tinha uma imagem antiga, deletar do Cloudinary
            if old_logo and old_logo != val and 'cloudinary.com' in old_logo:
                delete_cloudinary_image(old_logo, loja_slug)
            
            loja.logo = val[:200] if val else ''
            update_fields.append('logo')
        
        # Processar login_background
        if 'login_background' in request.data:
            val = (request.data.get('login_background') or '').strip()
            old_background = (loja.login_background or '').strip()
            
            # Se mudou e tinha uma imagem antiga, deletar do Cloudinary
            if old_background and old_background != val and 'cloudinary.com' in old_background:
                delete_cloudinary_image(old_background, loja_slug)
            
            loja.login_background = val[:200] if val else ''
            update_fields.append('login_background')
        
        # Processar login_logo
        if 'login_logo' in request.data:
            val = (request.data.get('login_logo') or '').strip()
            old_login_logo = (loja.login_logo or '').strip()
            
            # Se mudou e tinha uma imagem antiga, deletar do Cloudinary
            if old_login_logo and old_login_logo != val and 'cloudinary.com' in old_login_logo:
                delete_cloudinary_image(old_login_logo, loja_slug)
            
            loja.login_logo = val[:200] if val else ''
            update_fields.append('login_logo')
        
        # Processar cores
        if 'cor_primaria' in request.data:
            val = (request.data.get('cor_primaria') or '').strip()
            if val and val.startswith('#') and len(val) <= 7:
                loja.cor_primaria = val[:7]
                update_fields.append('cor_primaria')
        if 'cor_secundaria' in request.data:
            val = (request.data.get('cor_secundaria') or '').strip()
            if val and val.startswith('#') and len(val) <= 7:
                loja.cor_secundaria = val[:7]
                update_fields.append('cor_secundaria')
        
        loja.save(update_fields=update_fields)
        
        # Limpar cache
        from django.core.cache import cache
        cache_key = f'loja_info_publica:{loja.slug}'
        cache.delete(cache_key)
        
        return Response({
            'logo': (loja.logo or '').strip(),
            'login_background': (loja.login_background or '').strip(),
            'login_logo': (loja.login_logo or '').strip(),
            'cor_primaria': loja.cor_primaria or '#10B981',
            'cor_secundaria': loja.cor_secundaria or '#059669',
        })

