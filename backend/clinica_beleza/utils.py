"""
Utilitários compartilhados para Clínica da Beleza
"""
from tenants.middleware import get_current_loja_id
from django.core.cache import cache


class LojaContextHelper:
    """Helper para contexto de loja com cache automático"""
    
    @staticmethod
    def get_owner_professional_id():
        """
        Retorna ID do Professional vinculado ao owner da loja atual.
        Usa cache de 1 hora para melhor performance.
        """
        loja_id = get_current_loja_id()
        if not loja_id:
            return None
        
        cache_key = f'owner_professional_{loja_id}'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        
        try:
            from superadmin.models import Loja, ProfissionalUsuario
            loja = Loja.objects.using('default').get(id=loja_id)
            pu = ProfissionalUsuario.objects.using('default').filter(
                loja_id=loja_id, user_id=loja.owner_id
            ).first()
            result = pu.professional_id if pu else None
            cache.set(cache_key, result, 3600)  # 1 hora
            return result
        except Exception:
            return None
    
    @staticmethod
    def get_loja_owner_info():
        """
        Retorna dados do administrador da loja atual.
        Usa cache de 1 hora para melhor performance.
        """
        loja_id = get_current_loja_id()
        if not loja_id:
            return None
        
        cache_key = f'loja_owner_info_{loja_id}'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        
        try:
            from superadmin.models import Loja
            loja = Loja.objects.using('default').select_related('owner').get(id=loja_id)
            result = {
                'owner_username': loja.owner.username,
                'owner_email': loja.owner.email or '',
                'owner_telefone': getattr(loja, 'owner_telefone', '') or '',
            }
            cache.set(cache_key, result, 3600)  # 1 hora
            return result
        except Exception:
            return None
    
    @staticmethod
    def get_whatsapp_config(loja_id=None, request=None):
        """
        Retorna (config, loja) para a loja atual.
        Usa cache de 10 minutos para melhor performance.
        """
        lid = loja_id or get_current_loja_id()
        if not lid and request:
            try:
                lid = request.headers.get('X-Loja-ID')
                if lid:
                    lid = int(lid)
            except (ValueError, TypeError):
                lid = None
            if not lid and request.headers.get('X-Tenant-Slug'):
                from superadmin.models import Loja
                loja = Loja.objects.using('default').filter(
                    slug__iexact=request.headers.get('X-Tenant-Slug').strip()
                ).first()
                if loja:
                    lid = loja.id
        
        if not lid:
            return None, None
        
        cache_key = f'whatsapp_config_{lid}'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        
        try:
            from superadmin.models import Loja
            from whatsapp.models import WhatsAppConfig
            loja = Loja.objects.using('default').get(id=lid)
            config = getattr(loja, 'whatsapp_config', None) or \
                     WhatsAppConfig.objects.filter(loja=loja).first()
            result = (config, loja)
            cache.set(cache_key, result, 600)  # 10 minutos
            return result
        except Exception:
            return None, None
    
    @staticmethod
    def invalidate_cache(loja_id):
        """Invalida todos os caches da loja"""
        cache.delete(f'owner_professional_{loja_id}')
        cache.delete(f'loja_owner_info_{loja_id}')
        cache.delete(f'whatsapp_config_{loja_id}')
        # Invalida cache do dashboard
        from django.utils.timezone import now
        today = now().date()
        cache.delete(f'clinica_beleza_dashboard_{loja_id}_{today}')
