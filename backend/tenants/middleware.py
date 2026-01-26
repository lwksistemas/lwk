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

def get_current_loja_id():
    """Retorna o ID da loja atual"""
    return getattr(_thread_locals, 'current_loja_id', None)

def set_current_loja_id(loja_id):
    """Define o ID da loja atual"""
    _thread_locals.current_loja_id = loja_id

class TenantMiddleware:
    """
    Middleware que identifica o tenant pela URL ou header
    e configura o banco de dados correto
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        import logging
        logger = logging.getLogger(__name__)
        
        # Detectar tenant por subdomain, header ou parâmetro
        tenant_slug = self._get_tenant_slug(request)
        logger.info(f"🔍 [TenantMiddleware] URL: {request.path} | Slug detectado: {tenant_slug}")
        
        if tenant_slug:
            # Buscar a loja pelo slug
            from superadmin.models import Loja
            try:
                loja = Loja.objects.get(slug=tenant_slug)
                loja_id = loja.id
                
                # Configurar banco da loja
                db_name = f'loja_{tenant_slug}'
                
                # Verificar se o banco existe nas configurações
                if db_name in settings.DATABASES:
                    set_current_tenant_db(db_name)
                else:
                    # Banco não existe, usar default
                    set_current_tenant_db('default')
                
                # ✅ IMPORTANTE: Setar o loja_id no contexto para o LojaIsolationManager
                set_current_loja_id(loja_id)
                logger.info(f"✅ [TenantMiddleware] Contexto setado: loja_id={loja_id}, db={db_name}")
                
            except Loja.DoesNotExist:
                logger.warning(f"⚠️ [TenantMiddleware] Loja não encontrada: slug={tenant_slug}")
                set_current_tenant_db('default')
                set_current_loja_id(None)
        else:
            logger.debug(f"ℹ️ [TenantMiddleware] Nenhum slug detectado - usando default")
            set_current_tenant_db('default')
            set_current_loja_id(None)
        
        response = self.get_response(request)
        return response
    
    def _get_tenant_slug(self, request):
        """Extrai o slug do tenant da requisição"""
        import logging
        logger = logging.getLogger(__name__)
        
        # 1. Tentar pegar do header X-Loja-ID (PRIORIDADE - ID único)
        loja_id = request.headers.get('X-Loja-ID')
        logger.info(f"🔍 [_get_tenant_slug] X-Loja-ID header: {loja_id}")
        
        if loja_id:
            try:
                from superadmin.models import Loja
                loja = Loja.objects.get(id=int(loja_id))
                return loja.slug
            except (Loja.DoesNotExist, ValueError):
                pass
        
        # 2. Tentar pegar do header X-Tenant-Slug (fallback)
        tenant_slug = request.headers.get('X-Tenant-Slug')
        if tenant_slug:
            return tenant_slug
        
        # 3. Tentar pegar do parâmetro de query
        tenant_slug = request.GET.get('tenant')
        if tenant_slug:
            return tenant_slug
        
        # 4. Tentar pegar da URL (ex: /loja/linda/...)
        path_parts = request.path.split('/')
        if len(path_parts) >= 3 and path_parts[1] == 'loja':
            return path_parts[2]
        
        # 5. Tentar pegar do subdomain
        host = request.get_host().split(':')[0]
        parts = host.split('.')
        if len(parts) > 2:  # ex: loja1.localhost
            return parts[0]
        
        return None
