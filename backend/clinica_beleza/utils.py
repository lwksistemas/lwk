"""
Utilitários compartilhados para Clínica da Beleza
"""
from django.core.cache import cache

from tenants.middleware import get_current_loja_id


class LojaContextHelper:
    """Helper para contexto de loja com cache automático"""
    
    @staticmethod
    def get_admin_professional_ids() -> set:
        """
        Retorna set[int] com os professional_id de todos os administradores
        da loja atual (perfil='administrador') + owner. Cacheado por 1 hora.
        """
        loja_id = get_current_loja_id()
        if not loja_id:
            return set()

        cache_key = f'admin_professional_ids_{loja_id}'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            from superadmin.models import Loja, ProfissionalUsuario

            # Todos com perfil administrador na loja
            admin_ids = set(
                ProfissionalUsuario.objects.using('default')
                .filter(loja_id=loja_id, perfil='administrador')
                .values_list('professional_id', flat=True)
            )

            # Garantir owner sempre incluído (backward compat)
            try:
                loja = Loja.objects.using('default').get(id=loja_id)
                owner_pu = ProfissionalUsuario.objects.using('default').filter(
                    loja_id=loja_id, user_id=loja.owner_id
                ).first()
                if owner_pu:
                    admin_ids.add(owner_pu.professional_id)
            except Loja.DoesNotExist:
                pass

            cache.set(cache_key, admin_ids, 3600)
            return admin_ids
        except Exception:
            return set()

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
        Retorna dados do administrador e da loja atual.
        Usa cache de 1 hora para melhor performance.
        """
        loja_id = get_current_loja_id()
        if not loja_id:
            return None
        
        cache_key = f'loja_owner_info_v2_{loja_id}'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        
        try:
            from superadmin.models import Loja
            loja = Loja.objects.using('default').select_related('owner').get(id=loja_id)
            # Endereço formatado (sem CEP — CEP vai com telefone no recibo)
            partes_end = []
            if getattr(loja, 'logradouro', ''):
                end = loja.logradouro
                if getattr(loja, 'numero', ''):
                    end += f', {loja.numero}'
                partes_end.append(end)
            if getattr(loja, 'bairro', ''):
                partes_end.append(loja.bairro)
            if getattr(loja, 'cidade', ''):
                cidade = loja.cidade
                if getattr(loja, 'uf', ''):
                    cidade += f' - {loja.uf}'
                partes_end.append(cidade)

            result = {
                'owner_username': loja.owner.username,
                'owner_email': loja.owner.email or '',
                'owner_telefone': getattr(loja, 'owner_telefone', '') or '',
                # Dados da loja para recibos
                'nome': loja.nome or '',
                'cpf_cnpj': getattr(loja, 'cpf_cnpj', '') or '',
                'endereco': ', '.join(partes_end),
                'cep': getattr(loja, 'cep', '') or '',
                'telefone': getattr(loja, 'owner_telefone', '') or '',
                'email': loja.owner.email or '',
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
        from .views_base import resolve_loja_id_from_request

        lid = loja_id or get_current_loja_id()
        if not lid and request:
            lid = resolve_loja_id_from_request(request)
        
        if not lid:
            return None, None
        
        cache_key = f'whatsapp_config_{lid}'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        
        try:
            from superadmin.models import Loja
            from whatsapp.config_service import get_or_create_whatsapp_config

            loja = Loja.objects.using('default').get(id=lid)
            config = get_or_create_whatsapp_config(loja)
            if config:
                config._loja_cache = loja
            result = (config, loja)
            cache.set(cache_key, result, 600)  # 10 minutos
            return result
        except Exception:
            return None, None
    
    @staticmethod
    def invalidate_cache(loja_id):
        """Invalida todos os caches da loja"""
        cache.delete(f'owner_professional_{loja_id}')
        cache.delete(f'admin_professional_ids_{loja_id}')
        cache.delete(f'loja_owner_info_{loja_id}')
        cache.delete(f'whatsapp_config_{loja_id}')
        invalidate_dashboard_cache(loja_id)


DASHBOARD_CACHE_VERSION = 'v9'


def invalidate_dashboard_cache(loja_id, *, mes=None, ano=None, professional_id=None):
    """
    Limpa cache do dashboard para o mês informado (ou mês atual).
    Chamado após pagamentos, consultas e agendamentos.
    """
    from django.utils.timezone import now

    today = now().date()
    mes = mes or today.month
    ano = ano or today.year
    prof_key = str(professional_id) if professional_id else 'all'
    for period in ('hoje', 'semana', 'proximos'):
        cache.delete(
            f'clinica_beleza_dashboard_{DASHBOARD_CACHE_VERSION}_{loja_id}_{ano}_{mes:02d}_{period}_{prof_key}'
        )
        if prof_key != 'all':
            cache.delete(
                f'clinica_beleza_dashboard_{DASHBOARD_CACHE_VERSION}_{loja_id}_{ano}_{mes:02d}_{period}_all'
            )
