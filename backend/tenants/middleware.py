"""
Middleware para detectar o tenant (loja) e configurar o banco correto.
Aplica limite de tamanho (512 MB) no banco isolado por loja quando o arquivo existe.
"""
from pathlib import Path
from threading import local
from django.conf import settings
from django.http import JsonResponse
from django.db import connection
from django.utils import timezone

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
    
    OTIMIZAÇÃO: Cache de lojas para evitar queries repetidas
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self._loja_cache = {}  # Cache em memória {slug: loja_data}
    
    def __call__(self, request):
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Health check: responder AQUI sem passar por views/DRF/templates (evita 500 staticfiles no Render)
            if request.path.rstrip('/') == '/api/superadmin/health':
                set_current_tenant_db('default')
                set_current_loja_id(None)
                if request.method not in ('GET', 'HEAD'):
                    set_current_tenant_db('default')
                    return JsonResponse({'error': 'Method Not Allowed'}, status=405)
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT 1")
                        cursor.fetchone()
                    db_ok = True
                except Exception:
                    db_ok = False
                loja_count = None
                if db_ok:
                    try:
                        from superadmin.models import Loja
                        loja_count = Loja.objects.count()
                    except Exception:
                        pass
                status_code = 200 if db_ok else 503
                payload = {
                    'status': 'healthy' if db_ok else 'unhealthy',
                    'database': 'connected' if db_ok else 'disconnected',
                    'lojas_count': loja_count,
                    'timestamp': timezone.now().isoformat(),
                    'version': 'v750',
                }
                response = JsonResponse(payload, status=status_code)
                set_current_loja_id(None)
                set_current_tenant_db('default')
                return response
            # Detectar tenant por subdomain, header ou parâmetro
            tenant_slug = self._get_tenant_slug(request)
            
            if tenant_slug:
                # Buscar a loja pelo slug (case-insensitive: dani/Dani funcionam)
                from superadmin.models import Loja
                try:
                    # OTIMIZAÇÃO: Usar cache para evitar query repetida
                    cache_key = tenant_slug.lower()
                    
                    if cache_key in self._loja_cache:
                        loja_data = self._loja_cache[cache_key]
                        loja_id = loja_data['id']
                        db_name = loja_data['database_name']
                        logger.debug(f"✅ [TenantMiddleware] Loja {tenant_slug} encontrada no cache")
                    else:
                        loja = Loja.objects.filter(slug__iexact=tenant_slug).first()
                        if not loja:
                            raise Loja.DoesNotExist
                        
                        loja_id = loja.id
                        db_name = getattr(loja, 'database_name', None) or f'loja_{getattr(loja, "slug", tenant_slug)}'
                        
                        # Armazenar no cache
                        self._loja_cache[cache_key] = {
                            'id': loja_id,
                            'database_name': db_name,
                            'slug': loja.slug
                        }
                        logger.debug(f"✅ [TenantMiddleware] Loja {tenant_slug} adicionada ao cache")

                    # Configurar banco dinamicamente (SEMPRE reconfigurar para garantir schema correto)
                    try:
                        import dj_database_url
                        import os
                        DATABASE_URL = os.environ.get('DATABASE_URL')
                        if DATABASE_URL and db_name not in settings.DATABASES:
                            # CONN_MAX_AGE=0 para tenant: fecha conexão ao fim do request e evita "too many connections" no Postgres
                            default_db = dj_database_url.config(default=DATABASE_URL, conn_max_age=0)
                            # ✅ Usar database_name da loja (ex: loja_salao_000172) ao invés de loja_{id}
                            schema_name = db_name.replace('-', '_')
                            settings.DATABASES[db_name] = {
                                **default_db,
                                'OPTIONS': {
                                    'options': f'-c search_path={schema_name},public'
                                },
                                'ATOMIC_REQUESTS': False,
                                'AUTOCOMMIT': True,
                                'CONN_MAX_AGE': 0,
                                'CONN_HEALTH_CHECKS': False,
                                'TIME_ZONE': None,
                            }
                            logger.debug(f"✅ [TenantMiddleware] Banco '{db_name}' configurado com schema '{schema_name}'")
                    except Exception as db_err:
                        logger.warning("TenantMiddleware: falha ao configurar banco %s, usando default: %s", db_name, db_err)
                        db_name = 'default'

                    # Verificar se o banco existe nas configurações
                    if db_name in settings.DATABASES:
                        # Limite de tamanho: bloquear escritas se o arquivo SQLite da loja >= 512 MB
                        # NOTA: Isso só se aplica a SQLite local, não PostgreSQL em produção
                        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
                            db_path = getattr(settings, 'BASE_DIR', None)
                            # Verificar se é SQLite (não PostgreSQL)
                            if db_path is not None and 'sqlite' in str(settings.DATABASES.get(db_name, {}).get('ENGINE', '')):
                                path = Path(db_path) / f'db_{db_name}.sqlite3'
                                if path.exists():
                                    try:
                                        size = path.stat().st_size
                                        if size >= LIMITE_BANCO_LOJA_BYTES:
                                            logger.warning(
                                                f"⚠️ [TenantMiddleware] Loja {tenant_slug} atingiu limite "
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
                        set_current_tenant_db('default')

                    # Sempre setar loja_id para o LojaIsolationManager (funciona com default DB)
                    set_current_loja_id(loja_id)
                    logger.info(f"✅ [TenantMiddleware] Contexto setado: loja_id={loja_id}, db={getattr(_thread_locals, 'current_tenant_db', 'default')}")

                except Loja.DoesNotExist:
                    # Não logar aviso se for requisição de API sem tenant (ex: /api/superadmin/)
                    # Isso evita poluir logs com avisos desnecessários
                    if not request.path.startswith('/api/superadmin/') and not request.path.startswith('/api/suporte/'):
                        logger.warning(f"⚠️ [TenantMiddleware] Loja não encontrada: slug={tenant_slug}")
                    set_current_tenant_db('default')
                    set_current_loja_id(None)
                except Exception as e:
                    logger.exception("TenantMiddleware erro para slug=%s: %s", tenant_slug, e)
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
        
        # 5. Tentar pegar do subdomain (não usar para hosts de API backend)
        host = request.get_host().split(':')[0].lower()
        if host.endswith('.herokuapp.com') or '.onrender.com' in host:
            # Heroku/Render: o "subdomínio" é o nome do app, não slug de loja
            return None
        parts = host.split('.')
        if len(parts) > 2:  # ex: loja1.localhost
            tenant_slug = parts[0]
            # Nunca tratar nomes de serviço backend como slug de loja (evita query e erro de coluna)
            if tenant_slug in ('lwksistemas-backup', 'lwksistemas-38ad47519238'):
                return None
            if hasattr(request, 'user') and request.user.is_authenticated:
                if not self._validate_user_owns_loja_by_slug(request, tenant_slug):
                    return None
            return tenant_slug
        
        return None
    
    def _validate_user_owns_loja(self, request, loja):
        """Valida que usuário autenticado é owner da loja (objeto Loja)"""
        import logging
        logger = logging.getLogger(__name__)
        
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            logger.warning("⚠️ Usuário não autenticado tentando acessar loja")
            return False
        
        # SuperAdmin pode acessar qualquer loja
        if request.user.is_superuser:
            return True
        
        # Validar owner
        if loja.owner_id != request.user.id:
            logger.warning(
                f"⚠️ Usuário {request.user.id} ({request.user.email}) não é owner da loja {loja.slug} (owner: {loja.owner_id})"
            )
            
            # 🔧 PERMITIR acesso se for funcionário da loja (Clínica, Restaurante, etc.)
            try:
                from clinica_estetica.models import Funcionario as FuncionarioClinica
                from restaurante.models import Funcionario as FuncionarioRestaurante
                from servicos.models import Funcionario as FuncionarioServicos
                
                # Verificar se é funcionário (Clínica Estética)
                is_funcionario_clinica = FuncionarioClinica.objects.all_without_filter().filter(
                    loja_id=loja.id,
                    email=request.user.email,
                    is_active=True
                ).exists()
                
                if is_funcionario_clinica:
                    return True
                
                # Verificar se é funcionário (Restaurante)
                is_funcionario_restaurante = FuncionarioRestaurante.objects.all_without_filter().filter(
                    loja_id=loja.id,
                    email=request.user.email,
                    is_active=True
                ).exists()
                
                if is_funcionario_restaurante:
                    return True
                
                # Verificar se é profissional/usuário da Clínica da Beleza (ProfissionalUsuario)
                from superadmin.models import ProfissionalUsuario
                is_profissional_loja = ProfissionalUsuario.objects.filter(
                    user=request.user,
                    loja=loja
                ).exists()
                if is_profissional_loja:
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