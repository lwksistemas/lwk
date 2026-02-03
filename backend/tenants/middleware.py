"""
Middleware para detectar o tenant (loja) e configurar o banco correto.
Aplica limite de tamanho (512 MB) no banco isolado por loja quando o arquivo existe.
"""
from pathlib import Path
from threading import local
from django.conf import settings
from django.http import JsonResponse

_thread_locals = local()

# Limite do banco isolado por loja (512 MB - recomendado para CRM, clínica, e-commerce leve)
LIMITE_BANCO_LOJA_MB = 512
LIMITE_BANCO_LOJA_BYTES = LIMITE_BANCO_LOJA_MB * 1024 * 1024

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
        
        try:
            # Detectar tenant por subdomain, header ou parâmetro
            tenant_slug = self._get_tenant_slug(request)
            logger.info(f"🔍 [TenantMiddleware] URL: {request.path} | Slug detectado: {tenant_slug}")
            
            if tenant_slug:
                # Buscar a loja pelo slug (case-insensitive: dani/Dani funcionam)
                from superadmin.models import Loja
                try:
                    loja = Loja.objects.filter(slug__iexact=tenant_slug).first()
                    if not loja:
                        raise Loja.DoesNotExist
                    loja_id = loja.id
                    # Usar database_name da loja (pode ser diferente do slug)
                    db_name = loja.database_name if loja.database_name else f'loja_{loja.slug}'
                    
                    # Verificar se o banco existe nas configurações
                    if db_name in settings.DATABASES:
                        # Limite de tamanho: bloquear escritas se o arquivo SQLite da loja >= 512 MB
                        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
                            db_path = getattr(settings, 'BASE_DIR', None)
                            if db_path is not None and loja.database_created and loja.database_name:
                                path = Path(db_path) / f'db_{loja.database_name}.sqlite3'
                                if path.exists():
                                    try:
                                        size = path.stat().st_size
                                        if size >= LIMITE_BANCO_LOJA_BYTES:
                                            logger.warning(
                                                f"⚠️ [TenantMiddleware] Loja {loja.slug} atingiu limite "
                                                f"de banco ({size / (1024*1024):.1f} MB >= {LIMITE_BANCO_LOJA_MB} MB)"
                                            )
                                            return JsonResponse(
                                                {
                                                    'error': (
                                                        f'Limite de armazenamento da loja atingido '
                                                        f'({LIMITE_BANCO_LOJA_MB} MB). '
                                                        'Entre em contato com o suporte para ampliar o plano.'
                                                    ),
                                                    'code': 'STORAGE_LIMIT_REACHED',
                                                    'limite_mb': LIMITE_BANCO_LOJA_MB,
                                                },
                                                status=507,
                                            )
                                    except OSError:
                                        pass
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
            
            # 🛡️ SEGURANÇA CRÍTICA: Limpar contexto após cada requisição
            # Previne vazamento de loja_id entre requisições
            # IMPORTANTE: Limpar DEPOIS de gerar a resposta, não no finally
            set_current_loja_id(None)
            set_current_tenant_db('default')
            logger.debug("🧹 [TenantMiddleware] Contexto limpo após requisição")
            
            return response
        except Exception as e:
            # Em caso de erro, limpar contexto e re-raise
            logger.error(f"❌ [TenantMiddleware] Erro: {e}")
            set_current_loja_id(None)
            set_current_tenant_db('default')
            raise
    
    def _get_tenant_slug(self, request):
        """
        Extrai o slug do tenant da requisição
        
        SEGURANÇA: Valida que o usuário autenticado pertence à loja solicitada
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # 1. Tentar pegar do header X-Loja-ID (PRIORIDADE - ID único)
        loja_id = request.headers.get('X-Loja-ID')
        logger.info(f"🔍 [_get_tenant_slug] X-Loja-ID header: {loja_id}")
        
        if loja_id:
            try:
                from superadmin.models import Loja
                loja = Loja.objects.get(id=int(loja_id))
                
                # SEGURANÇA: Validar que o usuário pertence a esta loja
                # IMPORTANTE: Só validar se o usuário estiver autenticado
                if hasattr(request, 'user') and request.user.is_authenticated:
                    if not self._validate_user_owns_loja(request, loja):
                        logger.warning(f"⚠️ [_get_tenant_slug] Usuário {request.user.id} não tem permissão para loja {loja_id}")
                        return None
                
                return loja.slug
            except (Loja.DoesNotExist, ValueError):
                logger.warning(f"⚠️ [_get_tenant_slug] Loja {loja_id} não encontrada")
                pass
        
        # 2. Tentar pegar do header X-Tenant-Slug (fallback, case-insensitive)
        tenant_slug = request.headers.get('X-Tenant-Slug')
        if tenant_slug:
            if hasattr(request, 'user') and request.user.is_authenticated:
                if not self._validate_user_owns_loja_by_slug(request, tenant_slug):
                    return None
            return tenant_slug.strip()
        
        # 3. Tentar pegar do parâmetro de query
        tenant_slug = request.GET.get('tenant')
        if tenant_slug:
            if hasattr(request, 'user') and request.user.is_authenticated:
                if not self._validate_user_owns_loja_by_slug(request, tenant_slug):
                    return None
            return tenant_slug
        
        # 4. Tentar pegar da URL (ex: /loja/linda/...)
        path_parts = request.path.split('/')
        if len(path_parts) >= 3 and path_parts[1] == 'loja':
            tenant_slug = path_parts[2]
            if hasattr(request, 'user') and request.user.is_authenticated:
                if not self._validate_user_owns_loja_by_slug(request, tenant_slug):
                    return None
            return tenant_slug
        
        # 5. Tentar pegar do subdomain
        host = request.get_host().split(':')[0]
        parts = host.split('.')
        if len(parts) > 2:  # ex: loja1.localhost
            tenant_slug = parts[0]
            if hasattr(request, 'user') and request.user.is_authenticated:
                if not self._validate_user_owns_loja_by_slug(request, tenant_slug):
                    return None
            return tenant_slug
        
        return None
    
    def _validate_user_owns_loja(self, request, loja):
        """Valida que usuário autenticado é owner da loja (objeto Loja)"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🔍 [_validate_user_owns_loja] Validando acesso - Loja: {loja.slug} (ID: {loja.id})")
        
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            logger.warning("⚠️ Usuário não autenticado tentando acessar loja")
            return False
        
        logger.info(f"🔍 [_validate_user_owns_loja] Usuário: {request.user.id} ({request.user.email})")
        logger.info(f"🔍 [_validate_user_owns_loja] Owner da loja: {loja.owner_id}")
        
        # SuperAdmin pode acessar qualquer loja
        if request.user.is_superuser:
            logger.info(f"✅ SuperAdmin acessando loja {loja.slug}")
            return True
        
        # Validar owner
        if loja.owner_id != request.user.id:
            logger.warning(
                f"⚠️ Usuário {request.user.id} ({request.user.email}) não é owner da loja {loja.slug} (owner: {loja.owner_id})"
            )
            
            # 🔧 PERMITIR acesso se for funcionário da loja (para CRM Vendas, Clínica, etc.)
            # Verificar se é funcionário em qualquer app
            try:
                from crm_vendas.models import Vendedor
                from clinica_estetica.models import Funcionario as FuncionarioClinica
                from restaurante.models import Funcionario as FuncionarioRestaurante
                from servicos.models import Funcionario as FuncionarioServicos
                
                logger.info(f"🔍 [_validate_user_owns_loja] Verificando se é vendedor/funcionário...")
                
                # Verificar se é vendedor (CRM Vendas)
                is_vendedor = Vendedor.objects.all_without_filter().filter(
                    loja_id=loja.id,
                    email=request.user.email,
                    is_active=True
                ).exists()
                
                logger.info(f"🔍 [_validate_user_owns_loja] É vendedor (CRM)? {is_vendedor}")
                
                if is_vendedor:
                    logger.info(f"✅ Usuário {request.user.id} é vendedor da loja {loja.slug}")
                    return True
                
                # Verificar se é funcionário (Clínica Estética)
                is_funcionario_clinica = FuncionarioClinica.objects.all_without_filter().filter(
                    loja_id=loja.id,
                    email=request.user.email,
                    is_active=True
                ).exists()
                
                logger.info(f"🔍 [_validate_user_owns_loja] É funcionário (Clínica)? {is_funcionario_clinica}")
                
                if is_funcionario_clinica:
                    logger.info(f"✅ Usuário {request.user.id} é funcionário da loja {loja.slug}")
                    return True
                
                # Verificar se é funcionário (Restaurante)
                is_funcionario_restaurante = FuncionarioRestaurante.objects.all_without_filter().filter(
                    loja_id=loja.id,
                    email=request.user.email,
                    is_active=True
                ).exists()
                
                logger.info(f"🔍 [_validate_user_owns_loja] É funcionário (Restaurante)? {is_funcionario_restaurante}")
                
                if is_funcionario_restaurante:
                    logger.info(f"✅ Usuário {request.user.id} é funcionário da loja {loja.slug}")
                    return True
                
                # Verificar se é funcionário (Serviços)
                # Nota: Serviços não usa LojaIsolationMixin, então não tem loja_id
                # Vamos pular essa verificação por enquanto
                
            except Exception as e:
                logger.error(f"❌ Erro ao verificar se é funcionário: {e}", exc_info=True)
            
            logger.critical(
                f"🚨 BLOQUEIO: Usuário {request.user.id} ({request.user.email}) "
                f"não tem permissão para loja {loja.slug} (ID: {loja.id})"
            )
            return False
        
        logger.info(f"✅ Usuário {request.user.id} validado para loja {loja.slug} (owner)")
        return True
    
    def _validate_user_owns_loja_by_slug(self, request, tenant_slug):
        """Valida que usuário autenticado é owner da loja (por slug)"""
        import logging
        logger = logging.getLogger(__name__)
        
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            logger.warning("⚠️ Usuário não autenticado tentando acessar loja")
            return False
        
        # SuperAdmin pode acessar qualquer loja
        if request.user.is_superuser:
            logger.debug(f"✅ SuperAdmin acessando loja {tenant_slug}")
            return True
        
        try:
            from superadmin.models import Loja
            loja = Loja.objects.filter(slug__iexact=tenant_slug).first()
            
            if not loja:
                logger.warning(f"⚠️ Loja não encontrada: {tenant_slug}")
                return False
            
            return self._validate_user_owns_loja(request, loja)
        except Exception as e:
            logger.error(f"❌ Erro ao validar owner: {e}")
            return False
