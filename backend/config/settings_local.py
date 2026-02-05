"""
Configurações para desenvolvimento local
Usa o banco PostgreSQL do Heroku (produção) para testes
"""
from .settings import *
import dj_database_url

# Sobrescrever DATABASES para usar PostgreSQL do Heroku
DATABASE_URL = config('DATABASE_URL', default='')

if DATABASE_URL:
    # Usar PostgreSQL do Heroku
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
    
    # Configurações adicionais do PostgreSQL
    DATABASES['default']['OPTIONS'] = {
        'sslmode': 'require',
    }
    
    print("✅ [Local] Usando PostgreSQL do Heroku")
else:
    print("⚠️ [Local] DATABASE_URL não configurado, usando SQLite")

# Debug ativado para desenvolvimento
DEBUG = True

# Hosts permitidos para desenvolvimento
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '192.168.15.30']

# CORS para desenvolvimento
CORS_ALLOW_ALL_ORIGINS = True

# Configuração de logging para desenvolvimento
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'tenants.middleware': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'core.mixins': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

print(f"✅ [Local] Settings carregado - DEBUG={DEBUG}")
