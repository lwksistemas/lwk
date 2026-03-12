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
    DASHBOARD = 'crm_dashboard'
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
    def invalidate_dashboard(cls, loja_id):
        """
        Invalida cache do dashboard para todos os vendedores.
        
        Args:
            loja_id: ID da loja
        """
        if not loja_id:
            return
        
        # Invalidar cache do owner
        cache.delete(cls.get_cache_key(cls.DASHBOARD, loja_id, owner=True))
        
        # Invalidar cache de todos os vendedores
        try:
            from superadmin.models import VendedorUsuario
            for vid in VendedorUsuario.objects.filter(loja_id=loja_id).values_list('vendedor_id', flat=True).distinct():
                cache.delete(cls.get_cache_key(cls.DASHBOARD, loja_id, vid))
        except Exception:
            pass
    
    @classmethod
    def invalidate_contas(cls, loja_id):
        """
        Invalida cache de contas para todos os vendedores.
        
        Args:
            loja_id: ID da loja
        """
        if not loja_id:
            return
        
        # Invalidar cache do owner
        cache.delete(cls.get_cache_key(cls.CONTAS, loja_id, None))
        
        # Invalidar cache de todos os vendedores
        try:
            from superadmin.models import VendedorUsuario
            for vid in VendedorUsuario.objects.filter(loja_id=loja_id).values_list('vendedor_id', flat=True).distinct():
                cache.delete(cls.get_cache_key(cls.CONTAS, loja_id, vid))
        except Exception:
            pass
    
    @classmethod
    def invalidate_leads(cls, loja_id):
        """
        Invalida cache de leads para todos os vendedores.
        
        Args:
            loja_id: ID da loja
        """
        if not loja_id:
            return
        
        # Invalidar cache do owner
        cache.delete(cls.get_cache_key(cls.LEADS, loja_id, None))
        
        # Invalidar cache de todos os vendedores
        try:
            from superadmin.models import VendedorUsuario
            for vid in VendedorUsuario.objects.filter(loja_id=loja_id).values_list('vendedor_id', flat=True).distinct():
                cache.delete(cls.get_cache_key(cls.LEADS, loja_id, vid))
        except Exception:
            pass
    
    @classmethod
    def invalidate_contatos(cls, loja_id):
        """
        Invalida cache de contatos para todos os vendedores.
        
        Args:
            loja_id: ID da loja
        """
        if not loja_id:
            return
        
        # Invalidar cache do owner
        cache.delete(cls.get_cache_key(cls.CONTATOS, loja_id, None))
        
        # Invalidar cache de todos os vendedores
        try:
            from superadmin.models import VendedorUsuario
            for vid in VendedorUsuario.objects.filter(loja_id=loja_id).values_list('vendedor_id', flat=True).distinct():
                cache.delete(cls.get_cache_key(cls.CONTATOS, loja_id, vid))
        except Exception:
            pass
    
    @classmethod
    def invalidate_oportunidades(cls, loja_id):
        """
        Invalida cache de oportunidades para todos os vendedores.
        
        Args:
            loja_id: ID da loja
        """
        if not loja_id:
            return
        
        # Invalidar cache do owner
        cache.delete(cls.get_cache_key(cls.OPORTUNIDADES, loja_id, None))
        
        # Invalidar cache de todos os vendedores
        try:
            from superadmin.models import VendedorUsuario
            for vid in VendedorUsuario.objects.filter(loja_id=loja_id).values_list('vendedor_id', flat=True).distinct():
                cache.delete(cls.get_cache_key(cls.OPORTUNIDADES, loja_id, vid))
        except Exception:
            pass
    
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
