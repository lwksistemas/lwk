"""
Gerenciador centralizado de cache do CRM Vendas.
Elimina código duplicado de invalidação de cache.
"""
from django.core.cache import cache


class CRMCacheManager:
    """
    Gerencia cache do CRM Vendas de forma centralizada.
    
    Prefixos de cache:
    - crm_dashboard: Dashboard principal
    - crm_contas_list: Lista de contas
    - crm_atividades: Lista de atividades
    - crm_atividades_v: Versão do cache de atividades
    """
    
    # Prefixos de cache
    # v5: destino da mescla = is_admin ou e-mail do owner (não só is_admin)
    DASHBOARD = 'crm_dashboard_v5'
    CONTAS = 'crm_contas_list'
    LEADS = 'crm_leads_list'
    CONTATOS = 'crm_contatos_list'
    OPORTUNIDADES = 'crm_oportunidades_list'
    ATIVIDADES = 'crm_atividades'
    ATIVIDADES_VERSION = 'crm_atividades_v'
    
    # TTL padrão
    DEFAULT_TTL = 120  # 2 minutos
    
    @classmethod
    def get_cache_key(cls, prefix, loja_id, vendedor_id=None, **kwargs):
        """
        Gera chave de cache consistente.
        
        Args:
            prefix: Prefixo do cache (ex: 'crm_dashboard')
            loja_id: ID da loja
            vendedor_id: ID do vendedor (None para owner)
            **kwargs: Parâmetros adicionais para a chave
        
        Returns:
            String com chave de cache
        """
        if not loja_id:
            return None
        
        key = f'{prefix}:{loja_id}'
        
        # Sempre incluir identificador de vendedor ou owner
        if vendedor_id is not None:
            key += f':{vendedor_id}'
        else:
            key += ':owner'
        
        # Adicionar parâmetros extras ordenados
        for k, v in sorted(kwargs.items()):
            if k != 'owner':
                key += f':{v}'
        
        return key
    
    @classmethod
    def _invalidate_for_prefix(cls, prefix, loja_id, owner_key_value=None):
        """
        Invalida cache para um prefixo, removendo chaves do owner e de todos os vendedores.
        
        Args:
            prefix: Prefixo do cache (ex: cls.CONTAS)
            loja_id: ID da loja
            owner_key_value: Valor para owner (None = owner, ou True para DASHBOARD)
        """
        if not loja_id:
            return
        cache.delete(cls.get_cache_key(prefix, loja_id, owner_key_value))
        try:
            from superadmin.models import VendedorUsuario
            for vid in VendedorUsuario.objects.filter(loja_id=loja_id).values_list('vendedor_id', flat=True).distinct():
                cache.delete(cls.get_cache_key(prefix, loja_id, vid))
        except Exception:
            pass

    @classmethod
    def invalidate_dashboard(cls, loja_id):
        """Invalida cache do dashboard para todos os vendedores."""
        cls._invalidate_for_prefix(cls.DASHBOARD, loja_id, None)

    @classmethod
    def invalidate_contas(cls, loja_id):
        """Invalida cache de contas para todos os vendedores."""
        cls._invalidate_for_prefix(cls.CONTAS, loja_id, None)

    @classmethod
    def invalidate_leads(cls, loja_id):
        """Invalida cache de leads para todos os vendedores."""
        cls._invalidate_for_prefix(cls.LEADS, loja_id, None)

    @classmethod
    def invalidate_contatos(cls, loja_id):
        """Invalida cache de contatos para todos os vendedores."""
        cls._invalidate_for_prefix(cls.CONTATOS, loja_id, None)

    @classmethod
    def invalidate_oportunidades(cls, loja_id):
        """Invalida cache de oportunidades para todos os vendedores."""
        cls._invalidate_for_prefix(cls.OPORTUNIDADES, loja_id, None)
    
    @classmethod
    def invalidate_atividades(cls, loja_id):
        """
        Invalida cache de atividades incrementando versão.
        
        Usa estratégia de versionamento para invalidar todas as
        variações de cache de atividades (diferentes filtros).
        
        Args:
            loja_id: ID da loja
        """
        if not loja_id:
            return
        try:
            version_key = cls.get_cache_key(cls.ATIVIDADES_VERSION, loja_id)
            v = cache.get(version_key, 0) + 1
            cache.set(version_key, v, 86400)  # 24 horas
        except Exception:
            pass
    
    @classmethod
    def invalidate(cls, cache_key_name, loja_id=None):
        """
        Método genérico para invalidar cache por nome da chave.
        
        Mapeia nomes de chaves para métodos específicos de invalidação.
        Usado pelo CacheInvalidationMixin.
        
        Args:
            cache_key_name: Nome da chave (ex: 'oportunidades', 'dashboard')
            loja_id: ID da loja (obtido do contexto se None)
        """
        # Mapeamento de nomes para métodos
        invalidation_map = {
            'dashboard': cls.invalidate_dashboard,
            'contas': cls.invalidate_contas,
            'leads': cls.invalidate_leads,
            'contatos': cls.invalidate_contatos,
            'oportunidades': cls.invalidate_oportunidades,
            'atividades': cls.invalidate_atividades,
        }
        
        # Obter loja_id do contexto se não fornecido (fonte canônica: tenants.middleware)
        if loja_id is None:
            from tenants.middleware import get_current_loja_id
            loja_id = get_current_loja_id()
        
        if not loja_id:
            return
        
        # Chamar método específico
        invalidate_method = invalidation_map.get(cache_key_name)
        if invalidate_method:
            invalidate_method(loja_id)
    
    @classmethod
    def get_or_set(cls, key, callback, ttl=None):
        """
        Get or set pattern para cache.
        
        Args:
            key: Chave do cache
            callback: Função para gerar dados se não estiver em cache
            ttl: Tempo de vida do cache (usa DEFAULT_TTL se None)
        
        Returns:
            Tuple (data, from_cache) onde from_cache indica se veio do cache
        """
        if not key:
            return callback(), False
        
        cached = cache.get(key)
        if cached is not None:
            return cached, True
        
        data = callback()
        cache.set(key, data, ttl or cls.DEFAULT_TTL)
        return data, False
