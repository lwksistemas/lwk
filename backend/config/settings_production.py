"""Configurações de produção para LWK Sistemas (PostgreSQL).
"""
import logging
import os
from datetime import timedelta
from pathlib import Path

import dj_database_url

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY deve estar configurada nas variáveis de ambiente!")
_INSECURE_KEY_PREFIX = "django-insecure-"
if SECRET_KEY.startswith(_INSECURE_KEY_PREFIX):
    raise ValueError(
        "SECRET_KEY inválida em produção: a chave não pode começar com 'django-insecure-'. "
        'Gere uma nova chave com: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"',
    )
if len(SECRET_KEY) < 50:
    raise ValueError(
        "SECRET_KEY muito curta para produção: use no mínimo 50 caracteres. "
        'Gere uma nova chave com: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"',
    )
DEBUG = False
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h.strip()]
if not ALLOWED_HOSTS:
    raise ValueError("ALLOWED_HOSTS deve estar configurada nas variáveis de ambiente!")
# Atrás do edge TLS do Railway/Vercel-like proxy, confiar em X-Forwarded-Proto
# para que request.is_secure() reflita HTTPS externo e habilite HSTS.
if os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("USE_FORWARDED_SSL", "").lower() in ("true", "1", "yes"):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# APPS
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_q",
    "core",  # App base com modelos abstratos
    "stores",
    "products",
    "suporte",
    "tenants",
    "superadmin",
    "asaas_integration",  # Integração com Asaas
    "nfse_integration.apps.NfseIntegrationConfig",  # NFS-e (emissão/listagem) — deve coincidir com config.settings
    "clinica_beleza.apps.ClinicaBelezaConfig",  # Clínica da Beleza (agenda, profissionais, etc.)
    "hotel.apps.HotelConfig",  # App de hotelaria (Hotel / Pousada)
    "cabeleireiro.apps.CabeleireiroConfig",  # Salão de cabeleireiro (Lumina)
    "notificacoes.apps.NotificacoesConfig",  # Base de notificações (in-app, push, email, etc.)
    "push.apps.PushConfig",  # Push notifications (VAPID)
    "whatsapp.apps.WhatsappConfig",  # WhatsApp oficial (Meta Cloud API) - ETAPA 4
    "rules.apps.RulesConfig",  # Motor de regras automáticas - ETAPA 5
    "crm_vendas.apps.CrmVendasConfig",  # CRM Vendas (Leads, Oportunidades, Pipeline)
    "homepage.apps.HomepageConfig",  # Homepage configurável (hero, funcionalidades, módulos)
]

# MIDDLEWARE - JWT deve rodar ANTES do TenantMiddleware para X-Loja-ID funcionar
# CorsFallbackMiddleware: garante CORS em respostas /api/ quando corsheaders não adiciona (ex: 401/500)
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "config.cors_fallback_middleware.CorsFallbackMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "superadmin.middleware.JWTAuthenticationMiddleware",  # JWT antes do Tenant (X-Loja-ID)
    "tenants.middleware.TenantMiddleware",  # Requer usuário autenticado para validar loja
    "superadmin.middleware.SuperAdminSecurityMiddleware",  # APÓS AUTENTICAÇÃO
    "superadmin.middleware.inadimplencia.LojaInadimplenciaMiddleware",
    "core.middleware.response_cache.ResponseCacheMiddleware",  # ✅ Cache de respostas GET (Redis)
    "superadmin.historico_middleware.HistoricoAcessoMiddleware",  # ✅ Histórico de acessos
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

# TEMPLATES
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


def _normalize_database_url(raw: str) -> str:
    """URI completa postgres://... ou postgresql://...
    Se faltar o esquema (só user:pass@host...), urlparse usa o user como "scheme" e dj_database_url falha
    (ex.: No support for 'ufqqlop2dk1g7n').
    """
    s = (raw or "").strip()
    if not s:
        return s
    if s.startswith("//") and "@" in s:
        s = "postgres:" + s
    if "://" not in s and "@" in s:
        userinfo, _, rest = s.partition("@")
        if ":" in userinfo:
            s = "postgres://" + s
    return s


def _railway_public_proxy_ssl(url: str) -> str:
    """Proxy público Railway (*.rlwy.net): TLS obrigatório na conexão TCP."""
    s = (url or "").strip()
    if not s or ".rlwy.net" not in s.lower():
        return s
    if "sslmode=" in s.lower():
        return s
    return s + ("&" if "?" in s else "?") + "sslmode=require"


# DATABASE - PostgreSQL (produção). Sem DATABASE_URL válida: SQLite em /tmp (ex.: collectstatic em CI).
# DATABASE_URL pode existir como chave mas com valor vazio/inválido — dj_database_url levanta ValueError.
_database_url = _railway_public_proxy_ssl(_normalize_database_url(os.environ.get("DATABASE_URL") or ""))
_use_postgres = False
if _database_url:
    try:
        dj_database_url.parse(_database_url)
        _use_postgres = True
    except ValueError as exc:
        logger.warning(
            "DATABASE_URL ignorada (inválida). Use a URI completa: postgres://usuario:password@host:5432/nomebd "
            "(tem de começar por postgres:// ou postgresql://). Erro: %s",
            exc,
        )

if _use_postgres:
    DATABASES = {
        "default": dj_database_url.config(
            default=_database_url,
            conn_max_age=int(os.environ.get("CONN_MAX_AGE", "120")),
            conn_health_checks=True,
        ),
    }
    DATABASES["default"].setdefault("ATOMIC_REQUESTS", False)
    DATABASES["default"].setdefault("TIME_ZONE", None)
    if "OPTIONS" not in DATABASES["default"]:
        DATABASES["default"]["OPTIONS"] = {}
    _engine = DATABASES["default"].get("ENGINE", "")
    if "postgresql" in _engine:
        DATABASES["default"]["OPTIONS"]["connect_timeout"] = 10
        DATABASES["default"]["OPTIONS"]["options"] = "-c statement_timeout=25000"
        # Proxy público Railway (*.rlwy.net) exige TLS; sem sslmode o Postgres encerra a conexão.
        _pg_host = (DATABASES["default"].get("HOST") or "").lower()
        if _pg_host.endswith(".rlwy.net"):
            DATABASES["default"]["OPTIONS"].setdefault("sslmode", "require")
    DATABASE_ROUTERS = ["config.db_router.MultiTenantRouter"]
    _default_db = dict(DATABASES["default"])
    DATABASES["suporte"] = {
        **_default_db,
        "OPTIONS": {
            **_default_db.get("OPTIONS", {}),
            "options": "-c search_path=suporte,public -c statement_timeout=25000",
        },
    }
    if "postgresql" in _engine:
        _pg_host = (DATABASES["default"].get("HOST") or "").lower()
        if _pg_host.endswith(".rlwy.net"):
            DATABASES["suporte"]["OPTIONS"].setdefault("sslmode", "require")
else:
    logger.warning(
        "A usar SQLite em /tmp (sem Postgres válido). Para produção, defina DATABASE_URL com a URI PostgreSQL.",
    )
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": "/tmp/lwk-build-default.sqlite3",
            "ATOMIC_REQUESTS": False,
        },
        "suporte": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": "/tmp/lwk-build-suporte.sqlite3",
            "ATOMIC_REQUESTS": False,
        },
    }
    DATABASE_ROUTERS = ["config.db_router.MultiTenantRouter"]

# CACHE - Redis só se USE_REDIS=true e REDIS_URL existir (evita django_redis com Redis parado).
_use_redis_env = os.environ.get("USE_REDIS", "false").lower() in ("true", "1", "yes")
_redis_url = os.environ.get("REDIS_URL")
if _use_redis_env and _redis_url:
    _redis_options = {"CLIENT_CLASS": "django_redis.client.DefaultClient"}
    _pool_kwargs = {
        "max_connections": 50,
        "retry_on_timeout": True,
    }
    if _redis_url.startswith("rediss://"):
        import ssl

        import certifi

        _pool_kwargs["ssl_cert_reqs"] = ssl.CERT_REQUIRED
        _pool_kwargs["ssl_ca_certs"] = certifi.where()
    _redis_options["CONNECTION_POOL_KWARGS"] = _pool_kwargs
    _redis_options["SOCKET_CONNECT_TIMEOUT"] = 5
    _redis_options["SOCKET_TIMEOUT"] = 5
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": _redis_url,
            "OPTIONS": _redis_options,
            "KEY_PREFIX": "lwk",
            "TIMEOUT": 300,  # 5 minutos padrão (alinhado com CRMCacheManager.DEFAULT_TTL)
        },
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "lwk-cache",
            "OPTIONS": {
                "MAX_ENTRIES": 10000,
            },
        },
    }

USE_REDIS = _use_redis_env and bool(_redis_url)

# PASSWORD VALIDATION
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# INTERNATIONALIZATION
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# STATIC FILES
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# Sem manifest no disco → storage sem manifest (evita 500 em Browsable API / {% static %})
_disable_manifest = os.environ.get("DISABLE_STATICFILES_MANIFEST", "").lower() in ("true", "1", "yes")
_manifest_exists = (STATIC_ROOT / "staticfiles.json").exists()
if _disable_manifest or not _manifest_exists:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
else:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# MEDIA FILES
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# DEFAULT PRIMARY KEY
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CORS: domínio principal + lista em CORS_ORIGINS (separada por vírgula)
_DEFAULT_CORS_ORIGINS = [
    "https://lwksistemas.com.br",
    "https://www.lwksistemas.com.br",
    "https://beta.lwksistemas.com.br",
]
_raw = os.environ.get("CORS_ORIGINS", "").strip()
_extra_cors = [o.strip() for o in _raw.split(",") if o.strip()] if _raw else []
CORS_ALLOWED_ORIGINS = list(dict.fromkeys(_DEFAULT_CORS_ORIGINS + _extra_cors))
CORS_ALLOWED_ORIGIN_REGEXES = []
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False  # Manter segurança

# Front (lwksistemas.com.br) e API (api.lwksistemas.com.br) são origens diferentes.
# Views Django “puras” (sem @api_view) precisam disso no CSRF Origin check.
CSRF_TRUSTED_ORIGINS = list(CORS_ALLOWED_ORIGINS)

# ✅ CORREÇÃO v764: Adicionar configurações CORS necessárias para preflight
CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]
CORS_PREFLIGHT_MAX_AGE = 86400  # 24 horas (cache de preflight)

# CORS_ALLOW_HEADERS - Lista de headers permitidos nas requisições CORS
from corsheaders.defaults import default_headers

CORS_ALLOW_HEADERS = list(default_headers) + [
    "x-loja-id",  # ✅ Header customizado com ID único da loja
    "x-tenant-slug",  # ✅ Header customizado com slug da loja (fallback quando não tem ID)
    "x-session-id",  # ✅ Header para validação de sessão única (bloqueio simultâneo)
]

# REST FRAMEWORK
# Com DISABLE_STATICFILES_MANIFEST=true: desabilitar BrowsableAPIRenderer para evitar 500
# "Missing staticfiles manifest" em respostas HTML (templates usam {% static %}).
_drf_renderers = (
    "rest_framework.renderers.JSONRenderer",
)
if not _disable_manifest and _manifest_exists:
    _drf_renderers = (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    )

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "superadmin.authentication.SessionAwareJWTAuthentication",  # 🔐 SESSÃO ÚNICA
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_RENDERER_CLASSES": _drf_renderers,
    # Rate limiting: protege contra brute force no login
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        # SPA CRM dispara várias chamadas por tela; 200/min bloqueava listagens (ex.: propostas Felix).
        "anon": os.environ.get("DRF_THROTTLE_ANON_RATE", "500/hour"),
        "user": os.environ.get("DRF_THROTTLE_USER_RATE", "10000/hour"),
        "public_loja_create": "5/hour",
        "public_loja_lookup": "20/hour",
        "auth_login": "20/minute",
        "password_reset": "3/hour",
    },
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# JWT - Token de acesso curto para maior segurança
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),  # Access token curto (renovado pelo refresh)
    "REFRESH_TOKEN_LIFETIME": timedelta(hours=2),    # Sessão expira após 2h de inatividade
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

# EMAIL — Resend (API HTTP) ou Gmail SMTP (fallback legado)
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "").strip()

if RESEND_API_KEY:
    # Ignora EMAIL_HOST/USER/PASSWORD antigos do Gmail no Railway — usam só a API Resend
    EMAIL_BACKEND = "core.email_backends.ResendEmailBackend"
    DEFAULT_FROM_EMAIL = os.environ.get(
        "DEFAULT_FROM_EMAIL",
        "LWK Sistemas <noreply@lwksistemas.com.br>",
    )
else:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_USE_TLS = True
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
    EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "lwksistemas@gmail.com")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
    _smtp_user = EMAIL_HOST_USER or "lwksistemas@gmail.com"
    DEFAULT_FROM_EMAIL = os.environ.get(
        "DEFAULT_FROM_EMAIL",
        f"LWK Sistemas <{_smtp_user}>",
    )

DEFAULT_REPLY_TO = os.environ.get("DEFAULT_REPLY_TO", "contato@lwksistemas.com.br")

# SECURITY SETTINGS
# Railway (e similares): TLS termina no edge; o probe interno chama HTTP sem
# X-Forwarded-Proto → redirect 301 quebra o healthcheck e deixa deploy em FAILED.
if os.environ.get("RAILWAY_ENVIRONMENT"):
    SECURE_SSL_REDIRECT = False
else:
    SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_REFERRER_POLICY = "same-origin"
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ASAAS INTEGRATION
ASAAS_INTEGRATION_ENABLED = True
ASAAS_API_KEY = os.environ.get("ASAAS_API_KEY", "")
ASAAS_SANDBOX = os.environ.get("ASAAS_SANDBOX", "True").lower() == "true"
WEBHOOK_STRICT_VERIFY = os.environ.get("WEBHOOK_STRICT_VERIFY", "true").lower() in ("true", "1", "yes")
ASAAS_WEBHOOK_TOKEN = os.environ.get("ASAAS_WEBHOOK_TOKEN", "").strip()
ASAAS_LOJA_WEBHOOK_TOKEN = os.environ.get("ASAAS_LOJA_WEBHOOK_TOKEN", "").strip()
MERCADOPAGO_WEBHOOK_SECRET = os.environ.get("MERCADOPAGO_WEBHOOK_SECRET", "").strip()
SERVE_API_SCHEMA = os.environ.get("SERVE_API_SCHEMA", "false").lower() in ("true", "1", "yes")

# JWT em cookies httpOnly (frontend: NEXT_PUBLIC_JWT_HTTPONLY_COOKIES=true + withCredentials)
JWT_USE_HTTPONLY_COOKIES = os.environ.get("JWT_USE_HTTPONLY_COOKIES", "true").lower() in (
    "true", "1", "yes",
)
_jwt_domain = os.environ.get("JWT_COOKIE_DOMAIN", "").strip()
JWT_COOKIE_DOMAIN = _jwt_domain or None

# Helpers de segurança (slug, mensagens genéricas)
from config.security_helpers import GENERIC_AUTH_ERROR_MESSAGE, validate_store_slug  # noqa: F401

MFA_TOTP_ISSUER = os.environ.get("MFA_TOTP_ISSUER", "LWK Sistemas")
MFA_ENFORCE_TYPES = os.environ.get("MFA_ENFORCE_TYPES", "")  # ex: superadmin,suporte
FIELD_ENCRYPTION_KEY = os.environ.get("FIELD_ENCRYPTION_KEY", "").strip()
MIGRATION_GUARD_STRICT = os.environ.get("MIGRATION_GUARD_STRICT", "true").lower() in ("true", "1", "yes")

# MEMED — Prescrição digital (Clínica da Beleza). Docs: https://doc.memed.com.br/docs/backend-api
MEMED_API_KEY = os.environ.get("MEMED_API_KEY", "")
MEMED_SECRET_KEY = os.environ.get("MEMED_SECRET_KEY", "")
MEMED_ENVIRONMENT = os.environ.get("MEMED_ENVIRONMENT", "integration")  # 'integration' ou 'production'
MEMED_PRESCRITOR_ID = os.environ.get("MEMED_PRESCRITOR_ID", "")
MEMED_DEFAULT_UF = os.environ.get("MEMED_DEFAULT_UF", "")
# Chaves de PRODUÇÃO (prioridade quando MEMED_ENVIRONMENT=production; fallback p/ as genéricas).
MEMED_API_KEY_PROD = os.environ.get("MEMED_API_KEY_PROD", "")
MEMED_SECRET_KEY_PROD = os.environ.get("MEMED_SECRET_KEY_PROD", "")
MEMED_PRESCRITOR_ID_PROD = os.environ.get("MEMED_PRESCRITOR_ID_PROD", "")
# Auto-cadastro do prescritor na Memed ao salvar um profissional (POST de usuário).
# O endpoint de criação não está na doc pública da Memed — ative só depois de confirmar
# com o suporte de parceiros que sua conta tem permissão para criar prescritores via API.
MEMED_AUTO_CADASTRO = os.environ.get("MEMED_AUTO_CADASTRO", "false").strip().lower() in ("1", "true", "yes", "on")

# LOGGING
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

# ============================================
# DJANGO-Q CONFIGURATION (Task Queue)
# ============================================
from core.q_cluster_settings import build_q_cluster

_use_redis_for_queue = _use_redis_env and bool(_redis_url)
USE_TASK_QUEUE = os.environ.get("USE_TASK_QUEUE", "true" if _use_redis_for_queue else "false").lower() in (
    "true", "1", "yes",
)
# Broker Redis compartilhado entre backend (enfileira) e worker (consome).
Q_CLUSTER = build_q_cluster(
    workers=int(os.environ.get("DJANGO_Q_WORKERS", "4")),
    redis_url=_redis_url or None,
)

# Configurações de Notificações de Segurança
SECURITY_NOTIFICATION_EMAILS = os.environ.get(
    "SECURITY_NOTIFICATION_EMAILS",
    "",
).split(",") if os.environ.get("SECURITY_NOTIFICATION_EMAILS") else []
SITE_URL = os.environ.get("SITE_URL", "").rstrip("/")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://lwksistemas.com.br")
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.lwksistemas.com.br").rstrip("/")

# Google Calendar (OAuth2 + API) - CRM Vendas
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")

# WhatsApp Meta Cloud API + Evolution (WhatsApp Web)
WHATSAPP_API_URL = os.environ.get("WHATSAPP_API_URL", "https://graph.facebook.com/v19.0")
WHATSAPP_PHONE_ID = os.environ.get("WHATSAPP_PHONE_ID", "")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
EVOLUTION_API_URL = os.environ.get("EVOLUTION_API_URL", "").rstrip("/")
EVOLUTION_API_KEY = os.environ.get("EVOLUTION_API_KEY", "")
EVOLUTION_WEBHOOK_URL = os.environ.get("EVOLUTION_WEBHOOK_URL", "").rstrip("/")
LWK_ENVIRONMENT = os.environ.get("LWK_ENVIRONMENT", "production").strip().lower()
EVOLUTION_DEDICATED = os.environ.get("EVOLUTION_DEDICATED", "").lower() in ("true", "1", "yes")

# OpenAPI (drf-spectacular) — /api/schema/ (staff)
SPECTACULAR_SETTINGS = {
    "TITLE": "LWK Sistemas API",
    "DESCRIPTION": "API Multi-Tenant — superadmin, lojas, CRM, clínica, etc.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# Sentry (opcional — só ativa com SENTRY_DSN)
from config.sentry_init import init_sentry

init_sentry()
