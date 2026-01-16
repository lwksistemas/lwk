"""
Middleware para detectar o tenant (loja) e configurar o banco correto
"""
from threading import local
from django.conf import settings

_thread_locals = local()

def get_current_tenant_db():
    """Retorna o banco do tenant atual"""
    return getattr(_thread_locals, 'current_tenant_db', 'default')

def set_current_tenant_db(db_name):
    """Define o banco do tenant atual"""
    _thread_locals.current_tenant_db = db_name

class TenantMiddleware:
    """
    Middleware que identifica o tenant pela URL ou header
    e configura o banco de dados correto
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Detectar tenant por subdomain, header ou parâmetro
        tenant_slug = self._get_tenant_slug(request)
        
        if tenant_slug:
            # Configurar banco da loja
            db_name = f'loja_{tenant_slug}'
            
            # Verificar se o banco existe nas configurações
            if db_name in settings.DATABASES:
                set_current_tenant_db(db_name)
            else:
                # Banco não existe, usar default
                set_current_tenant_db('default')
        else:
            set_current_tenant_db('default')
        
        response = self.get_response(request)
        return response
    
    def _get_tenant_slug(self, request):
        """Extrai o slug do tenant da requisição"""
        # 1. Tentar pegar do header X-Tenant-Slug
        tenant_slug = request.headers.get('X-Tenant-Slug')
        if tenant_slug:
            return tenant_slug
        
        # 2. Tentar pegar do parâmetro de query
        tenant_slug = request.GET.get('tenant')
        if tenant_slug:
            return tenant_slug
        
        # 3. Tentar pegar do subdomain
        host = request.get_host().split(':')[0]
        parts = host.split('.')
        if len(parts) > 2:  # ex: loja1.localhost
            return parts[0]
        
        return None
