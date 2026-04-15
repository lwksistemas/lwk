"""
Configurações de Produção para LWK Sistemas
Otimizado para Heroku com PostgreSQL
"""
import logging
import os
import dj_database_url
from pathlib import Path
from datetime import timedelta
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY deve estar configurada nas variáveis de ambiente!")
DEBUG = False
ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', '').split(',') if h.strip()]
if not ALLOWED_HOSTS:
    raise ValueError("ALLOWED_HOSTS deve estar configurada nas variáveis de ambiente!")
# Plataforma Render: RENDER=true e/ou RENDER_SERVICE_ID (documentação Render).
_on_render = os.environ.get('RENDER', '').lower() in ('true', '1', 'yes') or bool(
    (os.environ.get('RENDER_SERVICE_ID') or '').strip()
)
# ".onrender.com" casa com qualquer *.onrender.com (Django).
# RENDER_EXTERNAL_HOSTNAME / URL: hostname público exato (evita 400 DisallowedHost).
if _on_render:
    if '.onrender.com' not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append('.onrender.com')
_render_ext_host = (os.environ.get('RENDER_EXTERNAL_HOSTNAME') or '').strip()
if _render_ext_host and _render_ext_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_render_ext_host)
_render_ext_url = (os.environ.get('RENDER_EXTERNAL_URL') or '').strip()
if _render_ext_url:
    try:
        _pu = urlparse(_render_ext_url).hostname
        if _pu and _pu not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(_pu)
    except Exception:
        pass
for _h in (os.environ.get('RENDER_ALLOWED_HOSTS_EXTRA') or '').split(','):
    _h = _h.strip()
    if _h and _h not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_h)
for _h in (os.environ.get('RENDER_EXTRA_ALLOWED_HOSTS') or '').split(','):
    _h = _h.strip()
    if _h and _h not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_h)
# Atrás de proxy TLS (Render, Heroku): scheme correto; evita comportamentos estranhos no SecurityMiddleware.
if _on_render or (os.environ.get('DYNO') or '').strip():
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
if _on_render:
    logger.info('Render: ALLOWED_HOSTS efetivo (sem segredos): %s', ALLOWED_HOSTS)

# APPS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'core',  # App base com modelos abstratos
    'stores',
    'products',
    'suporte',
    'tenants',
    'superadmin',
    'asaas_integration',  # Integração com Asaas
    'nfse_integration.apps.NfseIntegrationConfig',  # NFS-e (emissão/listagem) — deve coincidir com config.settings
    'clinica_estetica',
    'clinica_beleza.apps.ClinicaBelezaConfig',  # Clínica da Beleza (agenda, profissionais, etc.)
    'ecommerce',
    'restaurante',
    'servicos',
    'hotel.apps.HotelConfig',  # App de hotelaria (Hotel / Pousada)
    'cabeleireiro',  # App de cabeleireiro/salão de beleza
    'notificacoes.apps.NotificacoesConfig',  # Base de notificações (in-app, push, email, etc.)
    'push.apps.PushConfig',  # Push notifications (VAPID)
    'whatsapp.apps.WhatsappConfig',  # WhatsApp oficial (Meta Cloud API) - ETAPA 4
    'rules.apps.RulesConfig',  # Motor de regras automáticas - ETAPA 5
    'crm_vendas.apps.CrmVendasConfig',  # CRM Vendas (Leads, Oportunidades, Pipeline)
    'homepage.apps.HomepageConfig',  # Homepage configurável (hero, funcionalidades, módulos)
]

# MIDDLEWARE - JWT deve rodar ANTES do TenantMiddleware para X-Loja-ID funcionar
# CorsFallbackMiddleware: garante CORS em respostas /api/ quando corsheaders não adiciona (ex: 401/500)
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'config.cors_fallback_middleware.CorsFallbackMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'superadmin.middleware.JWTAuthenticationMiddleware',  # JWT antes do Tenant (X-Loja-ID)
    'tenants.middleware.TenantMiddleware',  # Requer usuário autenticado para validar loja
    'superadmin.middleware.SuperAdminSecurityMiddleware',  # APÓS AUTENTICAÇÃO
    'superadmin.historico_middleware.HistoricoAcessoMiddleware',  # ✅ Histórico de acessos
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

# TEMPLATES
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


def _normalize_database_url(raw: str) -> str:
    """
    Heroku/Render: URI completa postgres://... ou postgresql://...
    Se faltar o esquema (só user:pass@host...), urlparse usa o user como "scheme" e dj_database_url falha
    (ex.: No support for 'ufqqlop2dk1g7n').
    """
    s = (raw or '').strip()
    if not s:
        return s
    if s.startswith('//') and '@' in s:
        s = 'postgres:' + s
    if '://' not in s and '@' in s:
        userinfo, _, rest = s.partition('@')
        if ':' in userinfo:
            s = 'postgres://' + s
    return s


# DATABASE - PostgreSQL (produção). Sem DATABASE_URL válida: SQLite em /tmp (collectstatic no Render, etc.).
# No Render, DATABASE_URL pode existir como chave mas com valor vazio/inválido — dj_database_url rebenta com ValueError.
_database_url = _normalize_database_url(os.environ.get('DATABASE_URL') or '')
_use_postgres = False
if _database_url:
    try:
        dj_database_url.parse(_database_url)
        _use_postgres = True
    except ValueError as exc:
        logger.warning(
            'DATABASE_URL ignorada (inválida). No Render use a URI completa: postgres://usuario:password@host:5432/nomebd '
            '(tem de começar por postgres:// ou postgresql://). Erro: %s',
            exc,
        )

if _use_postgres:
    DATABASES = {
        'default': dj_database_url.config(
            default=_database_url,
            conn_max_age=int(os.environ.get('CONN_MAX_AGE', '60')),
            conn_health_checks=True,
        )
    }
    DATABASES['default'].setdefault('ATOMIC_REQUESTS', False)
    DATABASES['default'].setdefault('TIME_ZONE', None)
    if 'OPTIONS' not in DATABASES['default']:
        DATABASES['default']['OPTIONS'] = {}
    _engine = DATABASES['default'].get('ENGINE', '')
    if 'postgresql' in _engine:
        DATABASES['default']['OPTIONS']['connect_timeout'] = 10
        DATABASES['default']['OPTIONS']['options'] = '-c statement_timeout=25000'
    DATABASE_ROUTERS = ['config.db_router.MultiTenantRouter']
    _default_db = dict(DATABASES['default'])
    DATABASES['suporte'] = {
        **_default_db,
        'OPTIONS': {
            **_default_db.get('OPTIONS', {}),
            'options': '-c search_path=suporte,public -c statement_timeout=25000',
        },
    }
else:
    logger.warning(
        'A usar SQLite em /tmp (sem Postgres válido). Para produção, defina DATABASE_URL com a URI do Heroku.'
    )
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/tmp/lwk-build-default.sqlite3',
            'ATOMIC_REQUESTS': False,
        },
        'suporte': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/tmp/lwk-build-suporte.sqlite3',
            'ATOMIC_REQUESTS': False,
        },
    }
    DATABASE_ROUTERS = ['config.db_router.MultiTenantRouter']

# CACHE - Redis se REDIS_URL existir (Heroku Redis), senão LocMem (recomendação ANALISE_SEGURANCA_DESEMPENHO_CAPACIDADE.md)
# ✅ OTIMIZAÇÃO: Adicionado KEY_PREFIX, TIMEOUT, connection pool, socket timeouts e retry
_redis_url = os.environ.get('REDIS_URL')
if _redis_url:
    _redis_options = {'CLIENT_CLASS': 'django_redis.client.DefaultClient'}
    _pool_kwargs = {
        'max_connections': 50,
        'retry_on_timeout': True,
    }
    if _redis_url.startswith('rediss://'):
        _pool_kwargs['ssl_cert_reqs'] = None
    _redis_options['CONNECTION_POOL_KWARGS'] = _pool_kwargs
    _redis_options['SOCKET_CONNECT_TIMEOUT'] = 5
    _redis_options['SOCKET_TIMEOUT'] = 5
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': _redis_url,
            'OPTIONS': _redis_options,
            'KEY_PREFIX': 'lwk',
            'TIMEOUT': 300,  # 5 minutos padrão (alinhado com CRMCacheManager.DEFAULT_TTL)
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'lwk-cache',
            'OPTIONS': {
                'MAX_ENTRIES': 10000,
            }
        }
    }

# PASSWORD VALIDATION
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# INTERNATIONALIZATION
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# STATIC FILES
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
# No Render, manifest pode faltar (build efêmero); usar storage sem manifest evita 500 em respostas HTML da API
if os.environ.get('DISABLE_STATICFILES_MANIFEST', '').lower() in ('true', '1', 'yes'):
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
else:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# MEDIA FILES
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# DEFAULT PRIMARY KEY
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS (strip espaços; fallback para backup Render/Heroku)
_DEFAULT_CORS_ORIGINS = [
    'https://lwksistemas.com.br',
    'https://www.lwksistemas.com.br',
    'https://lwksistemas.vercel.app',
]
_raw = os.environ.get('CORS_ORIGINS', '').strip()
_extra_cors = [o.strip() for o in _raw.split(',') if o.strip()] if _raw else []
# União com defaults: CORS_ORIGINS só no Heroku não pode remover lwksistemas.com.br no Render após sync.
CORS_ALLOWED_ORIGINS = list(dict.fromkeys(_DEFAULT_CORS_ORIGINS + _extra_cors))
# Previews Vercel mudam a cada deploy (ex.: frontend-l21ck1pm9-lwks-projects-48afd555.vercel.app).
CORS_ALLOWED_ORIGIN_REGEXES = [
    r'^https://[a-z0-9-]+-lwks-projects-48afd555\.vercel\.app$',
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False  # Manter segurança

# ✅ CORREÇÃO v764: Adicionar configurações CORS necessárias para preflight
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
CORS_PREFLIGHT_MAX_AGE = 86400  # 24 horas (cache de preflight)

# CORS_ALLOW_HEADERS - Lista de headers permitidos nas requisições CORS
from corsheaders.defaults import default_headers
CORS_ALLOW_HEADERS = list(default_headers) + [
    'x-loja-id',  # ✅ Header customizado com ID único da loja
    'x-tenant-slug',  # ✅ Header customizado com slug da loja (fallback quando não tem ID)
]

# REST FRAMEWORK
# No Render (e onde DISABLE_STATICFILES_MANIFEST=true): desabilitar BrowsableAPIRenderer
# para evitar 500 "Missing staticfiles manifest" em respostas HTML (templates usam {% static %}).
_drf_renderers = (
    'rest_framework.renderers.JSONRenderer',
)
if not os.environ.get('DISABLE_STATICFILES_MANIFEST', '').lower() in ('true', '1', 'yes'):
    _drf_renderers = (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    )

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'superadmin.authentication.SessionAwareJWTAuthentication',  # 🔐 SESSÃO ÚNICA
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': _drf_renderers,
    # Throttle desabilitado - pode ser habilitado via variáveis de ambiente se necessário
    'DEFAULT_THROTTLE_CLASSES': [],
    'DEFAULT_THROTTLE_RATES': {
        'anon': os.environ.get('DRF_THROTTLE_ANON_RATE', '100000/hour'),
        'user': os.environ.get('DRF_THROTTLE_USER_RATE', '100000/hour'),
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}

# JWT - Token de acesso curto para maior segurança
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),  # Reduzido de 24h para 1h
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# EMAIL (Gmail SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'lwksistemas@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# SECURITY SETTINGS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ASAAS INTEGRATION
ASAAS_INTEGRATION_ENABLED = True
ASAAS_API_KEY = os.environ.get('ASAAS_API_KEY', '')
ASAAS_SANDBOX = os.environ.get('ASAAS_SANDBOX', 'True').lower() == 'true'

# LOGGING
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# ============================================
# DJANGO-Q CONFIGURATION (Task Queue)
# ============================================
Q_CLUSTER = {
    'name': 'LWKSistemas',
    'workers': int(os.environ.get('DJANGO_Q_WORKERS', '4')),
    'recycle': 500,
    'timeout': 300,  # 5 minutos
    'compress': True,
    'save_limit': 250,
    'queue_limit': 500,
    'cpu_affinity': 1,
    'label': 'Django Q',
    'redis': None,  # Usar ORM (PostgreSQL)
    'orm': 'default',
    'catch_up': True,
    'sync': False,
    'ack_failures': True,
    'max_attempts': 3,
    'retry': 360,  # 6 minutos (deve ser > timeout)
}

# Configurações de Notificações de Segurança
SECURITY_NOTIFICATION_EMAILS = os.environ.get(
    'SECURITY_NOTIFICATION_EMAILS',
    ''
).split(',') if os.environ.get('SECURITY_NOTIFICATION_EMAILS') else []
SITE_URL = os.environ.get('SITE_URL', 'https://lwksistemas-38ad47519238.herokuapp.com')
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://lwksistemas.com.br')

# Google Calendar (OAuth2 + API) - CRM Vendas
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
