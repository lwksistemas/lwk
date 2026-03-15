from pathlib import Path
from decouple import config
from datetime import timedelta
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-in-production-12345')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_spectacular',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',  # 🔐 SEGURANÇA: Blacklist para invalidar tokens
    'corsheaders',
    'django_q',  # ✅ Task queue para jobs agendados
    'core',  # App base com modelos abstratos
    'stores',
    'products',
    'suporte',  # App de suporte/chamados
    'tenants',  # App de gerenciamento de tenants
    'superadmin',  # App de super admin
    'asaas_integration',  # App de integração com Asaas
    'clinica_estetica',  # App de clínica de estética
    'ecommerce',  # App de e-commerce
    'restaurante',  # App de restaurante
    'servicos',  # App de serviços
    'cabeleireiro.apps.CabeleireiroConfig',  # App de cabeleireiro/salão de beleza
    'clinica_beleza.apps.ClinicaBelezaConfig',  # App de clínica da beleza
    'notificacoes.apps.NotificacoesConfig',  # Base de notificações (in-app, push, email, etc.)
    'push.apps.PushConfig',  # Push notifications (VAPID)
    'whatsapp.apps.WhatsappConfig',  # WhatsApp oficial (Meta Cloud API) - ETAPA 4
    'rules.apps.RulesConfig',  # Motor de regras automáticas - ETAPA 5
    'crm_vendas.apps.CrmVendasConfig',  # CRM Vendas (Leads, Oportunidades, Pipeline)
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.gzip.GZipMiddleware',  # ✅ OTIMIZAÇÃO: Compressão de resposta
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'config.security_middleware.SecurityIsolationMiddleware',
    'core.mixins.LojaContextMiddleware',
    'tenants.middleware.TenantMiddleware',
    'superadmin.historico_middleware.HistoricoAcessoMiddleware',  # ✅ Histórico de acessos
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

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

# ============================================
# CONFIGURAÇÃO MULTI-DATABASE (3 BANCOS ISOLADOS)
# ============================================

import dj_database_url

# Configuração padrão para desenvolvimento (SQLite)
DATABASES = {
    # BANCO 1: Super Admin (default) - Gerencia tudo
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_superadmin.sqlite3',
        # ✅ OTIMIZAÇÃO: Connection pooling
        'CONN_MAX_AGE': 600,  # Reutilizar conexões por 10 minutos
        'ATOMIC_REQUESTS': False,
        'OPTIONS': {
            'timeout': 20,
            'check_same_thread': False,
        }
    },
    
    # BANCO 2: Suporte - Sistema de chamados/tickets
    'suporte': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_suporte.sqlite3',
        # ✅ OTIMIZAÇÃO: Connection pooling
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'timeout': 20,
            'check_same_thread': False,
        }
    },
    
    # BANCO 3: Template para lojas (será clonado para cada loja)
    'loja_template': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_loja_template.sqlite3',
        # ✅ OTIMIZAÇÃO: Connection pooling
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'timeout': 20,
            'check_same_thread': False,
        }
    },
    
    # Bancos das lojas existentes
    'loja_loja-tech': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_loja_loja-tech.sqlite3',
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'timeout': 20,
            'check_same_thread': False,
        }
    },
    'loja_moda-store': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_loja_moda-store.sqlite3',
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'timeout': 20,
            'check_same_thread': False,
        }
    },
}

# ✅ CORREÇÃO v895: Configuração PostgreSQL para Produção (Heroku)
# Sobrescrever 'default' e 'suporte' se DATABASE_URL estiver presente
if 'DATABASE_URL' in os.environ:
    DATABASE_URL = os.environ['DATABASE_URL']
    
    default_db_config = dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=60,  # Reduzir de 600 para 60 segundos
        ssl_require=True,
        conn_health_checks=True,
    )
    
    # Configurar PostgreSQL com timeouts otimizados
    DATABASES['default'] = {
        **default_db_config,
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=25000',
        },
        'ATOMIC_REQUESTS': False,
        'AUTOCOMMIT': True,
        'CONN_HEALTH_CHECKS': True,
    }
    
    # ✅ Banco suporte: mesmo PostgreSQL, schema isolado (evita SQLite efêmero no Heroku)
    DATABASES['suporte'] = {
        **default_db_config,
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c search_path=suporte,public',
        },
        'ATOMIC_REQUESTS': False,
        'AUTOCOMMIT': True,
        'CONN_HEALTH_CHECKS': True,
    }
    
    print(f"✅ PostgreSQL configurado com timeouts otimizados")
    print(f"   - default: connect_timeout=10s, statement_timeout=25s")
    print(f"   - suporte: schema isolado (search_path=suporte,public)")

# Database Router para isolamento
DATABASE_ROUTERS = ['config.db_router.MultiTenantRouter']

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ✅ OTIMIZAÇÃO: Whitenoise otimizado
WHITENOISE_COMPRESS_OFFLINE = True
WHITENOISE_MAX_AGE = 31536000  # 1 ano de cache

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================
# REDIS CACHE CONFIGURATION
# ============================================
import os

USE_REDIS = os.environ.get('USE_REDIS', 'false').lower() == 'true'

if USE_REDIS:
    REDIS_URL = os.environ.get('REDIS_URL')
    if REDIS_URL:
        CACHES = {
            'default': {
                'BACKEND': 'django_redis.cache.RedisCache',
                'LOCATION': REDIS_URL,
                'OPTIONS': {
                    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                    'SOCKET_CONNECT_TIMEOUT': 5,
                    'SOCKET_TIMEOUT': 5,
                    'CONNECTION_POOL_KWARGS': {
                        'max_connections': 50,
                        'retry_on_timeout': True,
                    },
                },
                'KEY_PREFIX': 'lwk',
                'TIMEOUT': 300,  # 5 minutos padrão
            }
        }
        print("✅ Redis cache ativado:", REDIS_URL[:30] + "...")
    else:
        print("⚠️ USE_REDIS=true mas REDIS_URL não encontrado")
        # Fallback para LocMemCache
        CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'lwk-cache',
                'OPTIONS': {
                    'MAX_ENTRIES': 10000,
                }
            }
        }
else:
    # ✅ CACHE: Usando cache local em memória
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'lwk-cache',
            'OPTIONS': {
                'MAX_ENTRIES': 10000,
            }
        }
    }
    print("ℹ️ Redis cache desativado (USE_REDIS=false)")

# ✅ OTIMIZAÇÃO: GZip compression
GZIP_COMPRESSIBLE_TYPES = [
    'text/html',
    'text/css',
    'text/javascript',
    'application/javascript',
    'application/json',
]

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'superadmin.authentication.SessionAwareJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # Paginação otimizada para 40 lojas
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    # Throttling otimizado para 500 usuários simultâneos
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '10000/hour',  # 166 req/min = 2.7 req/seg por usuário (suporta 500 usuários)
    }
}

# drf-spectacular (OpenAPI / Swagger)
SPECTACULAR_SETTINGS = {
    'TITLE': 'LWK Sistemas API',
    'DESCRIPTION': 'API Multi-Tenant para gestão de lojas (superadmin, suporte, clinica, crm, restaurante, etc.)',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# CORS
CORS_ALLOWED_ORIGINS = config(
    'CORS_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000'
).split(',')
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False  # Nunca permitir todas as origens

# ✅ OTIMIZAÇÃO v663: Cache de preflight CORS por 24h
# Reduz requisições OPTIONS em 50% (navegador cacheia por 24h)
CORS_PREFLIGHT_MAX_AGE = 86400  # 24 horas em segundos

# Permitir headers customizados X-Loja-ID e X-Tenant-Slug
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-loja-id',  # ✅ Header customizado com ID único da loja
    'x-tenant-slug',  # ✅ Header customizado com slug da loja (fallback quando não tem ID)
]

# Expor headers customizados para o frontend
CORS_EXPOSE_HEADERS = [
    'content-type',
    'x-loja-id',
    'x-tenant-slug',
]

# Permitir métodos HTTP
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
# Email Settings
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='Sistema Multi-Loja <noreply@multloja.com>')

# Para desenvolvimento, usar console backend (mostra emails no terminal)
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Configurações de Notificações de Segurança
SECURITY_NOTIFICATION_EMAILS = config(
    'SECURITY_NOTIFICATION_EMAILS',
    default='',
    cast=lambda v: [email.strip() for email in v.split(',') if email.strip()]
)
SITE_URL = config('SITE_URL', default='http://localhost:3000')

# Nota Fiscal Asaas (emissão ao confirmar pagamento da assinatura)
# Serviço municipal conforme configuração da prefeitura da conta LWK no Asaas
ASAAS_INVOICE_SERVICE_CODE = config('ASAAS_INVOICE_SERVICE_CODE', default='')
ASAAS_INVOICE_SERVICE_NAME = config('ASAAS_INVOICE_SERVICE_NAME', default='Software sob demanda / Assinatura de sistema')
ASAAS_INVOICE_SERVICE_ID = config('ASAAS_INVOICE_SERVICE_ID', default='')

# ============================================
# DJANGO-Q CONFIGURATION (Task Queue)
# ============================================
Q_CLUSTER = {
    'name': 'LWKSistemas',
    'workers': 4,  # Número de workers paralelos
    'recycle': 500,  # Reciclar worker após N tarefas
    'timeout': 300,  # Timeout de 5 minutos por tarefa
    'compress': True,  # Comprimir dados na fila
    'save_limit': 250,  # Manter últimas 250 tarefas no histórico
    'queue_limit': 500,  # Limite de tarefas na fila
    'cpu_affinity': 1,  # CPU affinity
    'label': 'Django Q',
    'redis': None,  # Usar ORM (banco de dados) ao invés de Redis
    'orm': 'default',  # Usar banco 'default' para armazenar tarefas
    'catch_up': True,  # Executar tarefas perdidas ao reiniciar
    'sync': False,  # Executar de forma assíncrona (não bloquear)
    'ack_failures': True,  # Reconhecer falhas
    'max_attempts': 3,  # Tentar até 3 vezes em caso de falha
    'retry': 360,  # Aguardar 360s (6min) antes de retentar (deve ser > timeout)
}

# Push Notifications (VAPID) - chave privada no backend; chave pública no frontend (NEXT_PUBLIC_VAPID_PUBLIC_KEY)
VAPID_PRIVATE_KEY = config('VAPID_PRIVATE_KEY', default='')
VAPID_CLAIM_MAILTO = config('VAPID_CLAIM_MAILTO', default='mailto:admin@lwksistemas.com.br')

# WhatsApp oficial (Meta Cloud API) - ETAPA 4
WHATSAPP_API_URL = config('WHATSAPP_API_URL', default='https://graph.facebook.com/v19.0')
WHATSAPP_PHONE_ID = config('WHATSAPP_PHONE_ID', default='')
WHATSAPP_TOKEN = config('WHATSAPP_TOKEN', default='')

# Google Calendar (OAuth2 + API) - CRM Vendas
GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID', default='')
GOOGLE_CLIENT_SECRET = config('GOOGLE_CLIENT_SECRET', default='')
FRONTEND_URL = config('FRONTEND_URL', default='https://lwksistemas.com.br')  # Base URL do front (redirect pós-OAuth)
