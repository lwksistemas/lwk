"""
🔒 CONFIGURAÇÕES DE SEGURANÇA ADICIONAIS
Importar em settings.py ou settings_production.py
"""
from decouple import config

# ============================================
# SEGURANÇA CRÍTICA
# ============================================

# 🔐 SECRET_KEY obrigatória em produção
if not config('DEBUG', default=True, cast=bool):
    SECRET_KEY = config('SECRET_KEY')  # Vai falhar se não estiver definida
    if SECRET_KEY == 'django-insecure-dev-key-change-in-production-12345':
        raise ValueError("❌ SECRET_KEY padrão não pode ser usada em produção!")

# ============================================
# HTTPS E COOKIES SEGUROS
# ============================================

# Forçar HTTPS em produção
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Cookies seguros
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# ============================================
# HEADERS DE SEGURANÇA
# ============================================

# Prevenir clickjacking
X_FRAME_OPTIONS = 'DENY'

# Prevenir MIME sniffing
SECURE_CONTENT_TYPE_NOSNIFF = True

# Forçar navegadores a usar HTTPS
SECURE_HSTS_SECONDS = 31536000  # 1 ano
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# XSS Protection
SECURE_BROWSER_XSS_FILTER = True

# ============================================
# RATE LIMITING ESPECÍFICO POR ENDPOINT
# ============================================

# Configuração de throttling por endpoint
REST_FRAMEWORK_THROTTLE_RATES = {
    # Autenticação - muito restritivo
    'auth_login': '5/15min',  # 5 tentativas a cada 15 minutos
    'auth_refresh': '10/hour',
    'password_reset': '3/hour',
    
    # Operações normais
    'user': '2000/hour',
    'anon': '100/hour',
    
    # Operações pesadas
    'bulk_operations': '10/min',
    'reports': '30/hour',
}

# ============================================
# VALIDAÇÃO DE SLUG
# ============================================

import re

SLUG_VALIDATION_REGEX = re.compile(r'^[a-z0-9-]+$')

def validate_store_slug(slug):
    """
    Valida formato do slug da loja
    
    Regras:
    - Apenas letras minúsculas, números e hífens
    - Mínimo 3 caracteres
    - Máximo 50 caracteres
    """
    if not slug:
        raise ValueError("Slug não pode ser vazio")
    
    if len(slug) < 3:
        raise ValueError("Slug deve ter no mínimo 3 caracteres")
    
    if len(slug) > 50:
        raise ValueError("Slug deve ter no máximo 50 caracteres")
    
    if not SLUG_VALIDATION_REGEX.match(slug):
        raise ValueError("Slug deve conter apenas letras minúsculas, números e hífens")
    
    if slug.startswith('-') or slug.endswith('-'):
        raise ValueError("Slug não pode começar ou terminar com hífen")
    
    if '--' in slug:
        raise ValueError("Slug não pode conter hífens consecutivos")
    
    return True

# ============================================
# LOGGING DE SEGURANÇA
# ============================================

SECURITY_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'security': {
            'format': '[{levelname}] {asctime} {name} - {message}',
            'style': '{',
        },
    },
    'handlers': {
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/security.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'security',
        },
        'security_console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'security',
        },
    },
    'loggers': {
        'security': {
            'handlers': ['security_file', 'security_console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_file', 'security_console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# ============================================
# BLACKLIST DE TOKENS JWT
# ============================================

# Configurar blacklist para invalidar tokens no logout
SIMPLE_JWT_BLACKLIST_ENABLED = True

# ============================================
# PROTEÇÃO CONTRA CSRF EM BEACON
# ============================================

# Endpoints que aceitam beacon (sem CSRF)
CSRF_EXEMPT_BEACON_ENDPOINTS = [
    '/api/auth/logout/beacon/',
]

# ============================================
# VALIDAÇÃO DE ORIGEM
# ============================================

def validate_request_origin(request):
    """
    Valida origem do request para prevenir CSRF
    """
    origin = request.META.get('HTTP_ORIGIN', '')
    referer = request.META.get('HTTP_REFERER', '')
    
    allowed_origins = config(
        'CORS_ORIGINS',
        default='http://localhost:3000,http://127.0.0.1:3000'
    ).split(',')
    
    # Verificar se origem está na lista permitida
    if origin and origin not in allowed_origins:
        return False
    
    # Verificar referer como fallback
    if referer:
        for allowed in allowed_origins:
            if referer.startswith(allowed):
                return True
    
    return True if origin in allowed_origins else False

# ============================================
# CONFIGURAÇÃO DE SENHA
# ============================================

# Requisitos mínimos de senha
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_NUMBERS = True
PASSWORD_REQUIRE_SPECIAL = False

# Tempo de expiração de senha provisória (em horas)
PROVISIONAL_PASSWORD_EXPIRY_HOURS = 24

# ============================================
# AUDITORIA
# ============================================

# Eventos de segurança para auditar
SECURITY_AUDIT_EVENTS = [
    'login_success',
    'login_failure',
    'logout',
    'password_change',
    'password_reset',
    'permission_denied',
    'cross_tenant_access_attempt',
    'invalid_token',
    'session_expired',
]

# ============================================
# TIMEOUTS
# ============================================

# Timeout de sessão (em segundos)
SESSION_COOKIE_AGE = 3600  # 1 hora

# Timeout de inatividade (em minutos)
SESSION_INACTIVITY_TIMEOUT = 30

# ============================================
# PROTEÇÃO CONTRA ENUMERAÇÃO DE USUÁRIOS
# ============================================

# Usar mesma mensagem para usuário não encontrado e senha incorreta
GENERIC_AUTH_ERROR_MESSAGE = "Credenciais inválidas"

# ============================================
# CONFIGURAÇÃO DE CORS RESTRITIVA
# ============================================

# Métodos HTTP permitidos
CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'OPTIONS',
]

# Nunca permitir credenciais com CORS_ALLOW_ALL_ORIGINS
if config('CORS_ALLOW_ALL_ORIGINS', default=False, cast=bool):
    raise ValueError("❌ CORS_ALLOW_ALL_ORIGINS não pode ser True em produção!")
