from pathlib import Path
from decouple import config
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-in-production-12345')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,*').split(',')

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
    'suporte',  # App de suporte/chamados
    'tenants',  # App de gerenciamento de tenants
    'superadmin',  # App de super admin
    'asaas_integration',  # App de integração com Asaas
    'clinica_estetica',  # App de clínica de estética
    'crm_vendas',  # App de CRM vendas
    'ecommerce',  # App de e-commerce
    'restaurante',  # App de restaurante
    'servicos',  # App de serviços
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.gzip.GZipMiddleware',  # ✅ OTIMIZAÇÃO: Compressão de resposta
    'config.security_middleware.SecurityIsolationMiddleware',  # 🔐 SEGURANÇA: Isolamento dos 3 grupos
    'config.session_middleware.SessionControlMiddleware',  # 🔐 SEGURANÇA: Controle de sessão única
    'tenants.middleware.TenantMiddleware',  # Middleware customizado
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
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

# ✅ OTIMIZAÇÃO: Cache em memória (grátis!)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}

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
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,  # ✅ OTIMIZAÇÃO: Paginação padrão
    # ✅ OTIMIZAÇÃO: Throttling para prevenir abuso
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',  # 100 requisições por hora para não autenticados
        'user': '1000/hour'  # 1000 requisições por hora para autenticados
    }
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
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Apenas em desenvolvimento
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