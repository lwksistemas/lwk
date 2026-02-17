"""
Configurações de Produção para LWK Sistemas
Otimizado para Heroku com PostgreSQL
"""
import os
import dj_database_url
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY deve estar configurada nas variáveis de ambiente!")
DEBUG = False
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
if not ALLOWED_HOSTS or ALLOWED_HOSTS == ['']:
    raise ValueError("ALLOWED_HOSTS deve estar configurada nas variáveis de ambiente!")

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
    'django_q',  # ✅ Task queue para jobs agendados
    'core',  # App base com modelos abstratos
    'stores',
    'products',
    'suporte',
    'tenants',
    'superadmin',
    'asaas_integration',  # Integração com Asaas
    'clinica_estetica',
    'clinica_beleza.apps.ClinicaBelezaConfig',  # Clínica da Beleza (agenda, profissionais, etc.)
    'crm_vendas',
    'ecommerce',
    'restaurante',
    'servicos',
    'cabeleireiro',  # App de cabeleireiro/salão de beleza
    'notificacoes.apps.NotificacoesConfig',  # Base de notificações (in-app, push, email, etc.)
    'push.apps.PushConfig',  # Push notifications (VAPID)
    'whatsapp.apps.WhatsappConfig',  # WhatsApp oficial (Meta Cloud API) - ETAPA 4
    'rules.apps.RulesConfig',  # Motor de regras automáticas - ETAPA 5
]

# MIDDLEWARE
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'tenants.middleware.TenantMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'superadmin.middleware.JWTAuthenticationMiddleware',  # PROCESSA JWT ANTES
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

# DATABASE - PostgreSQL via Heroku
# conn_max_age reduzido para 60s para evitar "too many connections"
# Heroku Postgres tem limite de conexões por role
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=int(os.environ.get('CONN_MAX_AGE', '60')),  # 60 segundos (antes: 600)
        conn_health_checks=True,
    )
}

# Adicionar timeout de conexão para evitar conexões travadas
if 'OPTIONS' not in DATABASES['default']:
    DATABASES['default']['OPTIONS'] = {}
DATABASES['default']['OPTIONS']['connect_timeout'] = 10

# CACHE - Redis se REDIS_URL existir (Heroku Redis), senão LocMem (recomendação ANALISE_SEGURANCA_DESEMPENHO_CAPACIDADE.md)
_redis_url = os.environ.get('REDIS_URL')
if _redis_url:
    _redis_options = {'CLIENT_CLASS': 'django_redis.client.DefaultClient'}
    if _redis_url.startswith('rediss://'):
        _redis_options['CONNECTION_POOL_KWARGS'] = {'ssl_cert_reqs': None}
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': _redis_url,
            'OPTIONS': _redis_options,
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
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# MEDIA FILES
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# DEFAULT PRIMARY KEY
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS
CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ORIGINS',
    'https://lwksistemas.com.br,https://www.lwksistemas.com.br,https://frontend-r3q0a1lw4-lwks-projects-48afd555.vercel.app'
).split(',')
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False  # Manter segurança
# CORS_ALLOW_HEADERS - Lista de headers permitidos nas requisições CORS
# Nota: O nome correto é CORS_ALLOW_HEADERS (não CORS_ALLOWED_HEADERS)
from corsheaders.defaults import default_headers
CORS_ALLOW_HEADERS = list(default_headers) + [
    'x-loja-id',  # ✅ Header customizado com ID único da loja
    'x-tenant-slug',  # ✅ Header customizado com slug da loja (fallback quando não tem ID)
]

# REST FRAMEWORK
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'superadmin.authentication.SessionAwareJWTAuthentication',  # 🔐 SESSÃO ÚNICA
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    # Throttle em produção: limitar abuso; ajustável via env (ex.: heroku config:set DRF_THROTTLE_USER_RATE=3000/hour)
    'DEFAULT_THROTTLE_CLASSES': [
        # 'rest_framework.throttling.AnonRateThrottle',  # Desabilitado temporariamente
        # 'rest_framework.throttling.UserRateThrottle',  # Desabilitado temporariamente
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': os.environ.get('DRF_THROTTLE_ANON_RATE', '100000/hour'),  # Muito alto temporariamente
        'user': os.environ.get('DRF_THROTTLE_USER_RATE', '100000/hour'),  # Muito alto temporariamente
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
