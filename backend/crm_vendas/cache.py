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
    
    # Prefixos de versão para cada tipo de cache (mesmo padrão das atividades)
    CONTAS_VERSION        = 'crm_contas_v'
    LEADS_VERSION         = 'crm_leads_v'
    CONTATOS_VERSION      = 'crm_contatos_v'
    OPORTUNIDADES_VERSION = 'crm_opor_v'
    DASHBOARD_VERSION     = 'crm_dash_v'
    FINANCEIRO_VERSION    = 'crm_financeiro_v'

    # Prefixos de cache (dados em si)
    DASHBOARD    = 'crm_dashboard_v7'
    CONTAS       = 'crm_contas_list'
    LEADS        = 'crm_leads_list'
    CONTATOS     = 'crm_contatos_list'
    OPORTUNIDADES= 'crm_oportunidades_list'
    ATIVIDADES = 'crm_atividades'
    ATIVIDADES_VERSION = 'crm_atividades_v'
    
    # TTL padrão
    # ✅ OTIMIZAÇÃO v1490: Aumentado de 120s para 300s (5 minutos)
    # Melhora hit rate do Redis sem comprometer atualização de dados
    DEFAULT_TTL = 300  # 5 minutos
    
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
    
    # Mapa: prefix → versão correspondente (para invalidação por versão sem DB query)
    _PREFIX_VERSION_MAP = None  # inicializado como property para evitar referência circular

    @classmethod
    def _get_prefix_version_map(cls):
        return {
            cls.DASHBOARD:     cls.DASHBOARD_VERSION,
            cls.CONTAS:        cls.CONTAS_VERSION,
            cls.LEADS:         cls.LEADS_VERSION,
            cls.CONTATOS:      cls.CONTATOS_VERSION,
            cls.OPORTUNIDADES: cls.OPORTUNIDADES_VERSION,
        }

    @classmethod
    def _invalidate_for_prefix(cls, prefix, loja_id, owner_key_value=None):
        """
        Invalida cache por incremento de versão (sem DB query).
        O cache_list_response decorator inclui a versão na chave,
        tornando as chaves antigas automaticamente stale.
        """
        if not loja_id:
            return
        version_map = cls._get_prefix_version_map()
        version_key_prefix = version_map.get(prefix)
        if version_key_prefix:
            # Estratégia de versionamento: incrementar versão invalida
            # todas as variações de uma vez (owner + todos os vendedores)
            vkey = cls.get_cache_key(version_key_prefix, loja_id)
            v = cache.get(vkey, 0) + 1
            cache.set(vkey, v, 604800)  # 7 dias
        else:
            # Fallback para prefixes não mapeados (ex: financeiro)
            cache.delete(cls.get_cache_key(prefix, loja_id, owner_key_value))
            try:
                from superadmin.models import VendedorUsuario
                for vid in VendedorUsuario.objects.filter(
                    loja_id=loja_id
                ).values_list('vendedor_id', flat=True).distinct():
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
            # ✅ OTIMIZAÇÃO v1490: Aumentado de 24h para 7 dias
            cache.set(version_key, v, 604800)  # 7 dias
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
