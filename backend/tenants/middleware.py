"""Middleware para detectar o tenant (loja) e configurar o banco correto.
Aplica limite de tamanho (512 MB) no banco isolado por loja quando o arquivo existe.
"""
import logging
import os
from pathlib import Path
from threading import local

from django.conf import settings
from django.http import JsonResponse

logger = logging.getLogger(__name__)

_thread_locals = local()

# Limite do banco isolado por loja (512 MB - recomendado para CRM, clínica, e-commerce leve)
LIMITE_BANCO_LOJA_MB = 512
LIMITE_BANCO_LOJA_BYTES = LIMITE_BANCO_LOJA_MB * 1024 * 1024

def get_current_tenant_db():
    """Retorna o banco do tenant atual"""
    return getattr(_thread_locals, "current_tenant_db", "default")

def set_current_tenant_db(db_name):
    """Define o banco do tenant atual"""
    _thread_locals.current_tenant_db = db_name

def get_current_loja_id():
    """Retorna o ID da loja atual"""
    return getattr(_thread_locals, "current_loja_id", None)

def set_current_loja_id(loja_id):
    """Define o ID da loja atual"""
    _thread_locals.current_loja_id = loja_id


def _configure_tenant_db_for_loja(loja, request=None):
    """Configura database_name + thread-local (mesma lógica do TenantMiddleware).
    Sem isso, só loja_id no contexto consulta o schema/banco errado → listas vazias intermitentes.
    """
    loja_id = loja.id
    db_name = getattr(loja, "database_name", None) or f'loja_{getattr(loja, "slug", "")}'
    try:
        from core.db_config import ensure_loja_database_config
        if ensure_loja_database_config(db_name, conn_max_age=0):
            logger.debug("ensure_loja_context: banco '%s' configurado para loja_id=%s", db_name, loja_id)
    except Exception as db_err:
        logger.warning("ensure_loja_context: falha ao configurar banco %s: %s", db_name, db_err)
        db_name = "default"

    if db_name in settings.DATABASES:
        if request and request.method in ("POST", "PUT", "PATCH", "DELETE"):
            _base = getattr(settings, "BASE_DIR", None)
            if _base is not None and "sqlite" in str(settings.DATABASES.get(db_name, {}).get("ENGINE", "")):
                path = Path(_base) / f"db_{db_name}.sqlite3"
                if path.exists():
                    try:
                        if path.stat().st_size >= LIMITE_BANCO_LOJA_BYTES:
                            return False
                    except OSError:
                        pass
        set_current_tenant_db(db_name)
    else:
        set_current_tenant_db("default")

    set_current_loja_id(loja_id)
    return True


def resolve_loja_from_slug_or_cnpj(tenant_slug: str):
    """Resolve Loja pelo slug da URL (``Loja.slug``) ou, em último caso, pelo documento.

    Em produção o slug costuma ser o **CPF/CNPJ só com dígitos** (campo editável),
    ex.: ``41449198000172`` — o primeiro ``filter(slug__iexact=...)`` cobre isso.

    Se não houver linha com esse slug e o segmento tiver **11 ou 14 dígitos**, tenta
    match em ``cpf_cnpj`` normalizado (fallback para slugs legados ``nome-sufixo`` ou
    quando slug e documento divergiram).
    """
    import re

    from django.db import connection as django_connection

    from superadmin.models import Loja

    s = (tenant_slug or "").strip()
    if not s:
        return None

    loja = Loja.objects.using("default").filter(slug__iexact=s).first()
    if loja:
        return loja

    # Tentar por atalho (URL amigável)
    loja = Loja.objects.using("default").filter(atalho__iexact=s).first()
    if loja:
        return loja

    if not s.isdigit() or len(s) not in (11, 14):
        return None

    if django_connection.vendor == "postgresql":
        qn = django_connection.ops.quote_name(Loja._meta.db_table)
        with django_connection.cursor() as cursor:
            cursor.execute(
                f"SELECT id FROM {qn} WHERE regexp_replace(COALESCE(cpf_cnpj, ''), '[^0-9]', '', 'g') = %s LIMIT 1",
                [s],
            )
            row = cursor.fetchone()
            if row:
                return Loja.objects.using("default").get(pk=row[0])
    else:
        for candidate in (
            Loja.objects.using("default")
            .exclude(cpf_cnpj="")
            .exclude(cpf_cnpj__isnull=True)
            .iterator(chunk_size=500)
        ):
            if re.sub(r"\D", "", candidate.cpf_cnpj or "") == s:
                return candidate
    return None


def ensure_loja_context(request):
    """Garante loja_id + banco/schema do tenant a partir dos headers (alinhado ao TenantMiddleware).
    Quando há X-Loja-ID ou X-Tenant-Slug, reaplica a configuração (idempotente) para evitar
    só loja_id no thread-local sem o schema correto.
    """
    if not request:
        return False
    lid = (request.headers.get("X-Loja-ID") or "").strip()
    slug = (request.headers.get("X-Tenant-Slug") or "").strip()
    if not lid and not slug:
        return bool(get_current_loja_id())
    try:
        from superadmin.models import Loja
        loja = None
        # Slug primeiro: alinhado à URL do app; X-Loja-ID no navegador pode ficar desatualizado.
        if slug:
            loja = resolve_loja_from_slug_or_cnpj(slug)
        if not loja and lid:
            loja_id = int(lid)
            loja = Loja.objects.using("default").filter(id=loja_id).first()
        if loja:
            if hasattr(request, "user") and request.user.is_authenticated:
                from core.tenant_access import user_can_access_loja
                if not user_can_access_loja(request.user, loja):
                    set_current_loja_id(None)
                    set_current_tenant_db("default")
                    return False
            return _configure_tenant_db_for_loja(loja, request)
    except (ValueError, TypeError):
        pass
    return bool(get_current_loja_id())


class TenantMiddleware:
    """Middleware que identifica o tenant pela URL ou header
    e configura o banco de dados correto

    OTIMIZAÇÃO: Cache de lojas para evitar queries repetidas
    """

    # Limite do cache de lojas em memória (por worker) — evita crescimento ilimitado
    LOJA_CACHE_MAX = 1000

    def __init__(self, get_response):
        self.get_response = get_response
        self._loja_cache = {}  # Cache em memória {slug: loja_data}

    def __call__(self, request):
        # 🧹 LIMPAR contexto da requisição ANTERIOR no INÍCIO desta requisição
        set_current_loja_id(None)
        set_current_tenant_db("default")

        try:
            early = self._handle_early_returns(request)
            if early is not None:
                return early

            tenant_slug = self._get_tenant_slug(request)
            if tenant_slug:
                self._apply_tenant_context(request, tenant_slug)
            else:
                logger.debug("ℹ️ [TenantMiddleware] Nenhum slug detectado - usando default")

            return self.get_response(request)
        except Exception as e:
            logger.error(f"❌ [TenantMiddleware] Erro: {e}")
            raise
        finally:
            # ⚠️ NÃO limpar thread-local aqui!
            # A serialização DRF acontece APÓS o middleware retornar a response.
            pass

    def _handle_early_returns(self, request):
        """Trata health check e rotas de auth antes de resolver tenant. Retorna Response ou None."""
        if request.path.rstrip("/") == "/api/superadmin/health":
            set_current_tenant_db("default")
            set_current_loja_id(None)
            if request.method not in ("GET", "HEAD"):
                return JsonResponse({"error": "Method Not Allowed"}, status=405)
            from superadmin.views.sistema import health_check
            return health_check(request)

        path_norm = request.path.rstrip("/") or "/"
        if path_norm.startswith("/api/auth"):
            return self.get_response(request)

        from core.tenant_access import check_cross_tenant_access
        return check_cross_tenant_access(request)

    def _resolve_loja_from_cache_or_db(self, tenant_slug):
        """Retorna (loja_id, db_name) do cache em memória ou via DB. Lança Loja.DoesNotExist se não achar."""
        from superadmin.models import Loja

        cache_key = tenant_slug.lower()
        if cache_key in self._loja_cache:
            loja_data = self._loja_cache[cache_key]
            loja_id = loja_data["id"]
            db_name = loja_data["database_name"]
            if not Loja.objects.filter(id=loja_id).exists():
                logger.warning(f"⚠️ [TenantMiddleware] Loja {tenant_slug} (ID {loja_id}) foi excluída - removendo do cache")
                del self._loja_cache[cache_key]
                set_current_loja_id(None)
                set_current_tenant_db("default")
                raise Loja.DoesNotExist
            logger.debug(f"✅ [TenantMiddleware] Loja {tenant_slug} encontrada no cache")
            return loja_id, db_name

        loja = resolve_loja_from_slug_or_cnpj(tenant_slug)
        if not loja:
            raise Loja.DoesNotExist

        loja_id = loja.id
        db_name = getattr(loja, "database_name", None) or f'loja_{getattr(loja, "slug", tenant_slug)}'
        if len(self._loja_cache) >= self.LOJA_CACHE_MAX:
            self._loja_cache.clear()
        self._loja_cache[cache_key] = {"id": loja_id, "database_name": db_name, "slug": loja.slug}
        logger.debug(f"✅ [TenantMiddleware] Loja {tenant_slug} adicionada ao cache")
        return loja_id, db_name

    def _check_storage_limit(self, request, db_name, tenant_slug):
        """Bloqueia escritas se o arquivo SQLite da loja atingiu 512 MB. Retorna JsonResponse ou None."""
        if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
            return None
        db_path = getattr(settings, "BASE_DIR", None)
        if db_path is None or "sqlite" not in str(settings.DATABASES.get(db_name, {}).get("ENGINE", "")):
            return None
        path = Path(db_path) / f"db_{db_name}.sqlite3"
        if not path.exists():
            return None
        try:
            size = path.stat().st_size
        except OSError:
            return None
        if size < LIMITE_BANCO_LOJA_BYTES:
            return None
        logger.warning(
            f"⚠️ [TenantMiddleware] Loja {tenant_slug} atingiu limite "
            f"de banco ({size / (1024*1024):.1f} MB >= {LIMITE_BANCO_LOJA_MB} MB)",
        )
        return JsonResponse(
            {
                "error": f"Limite de armazenamento da loja atingido ({LIMITE_BANCO_LOJA_MB} MB). Entre em contato com o suporte para ampliar o plano.",
                "code": "STORAGE_LIMIT_REACHED",
                "limite_mb": LIMITE_BANCO_LOJA_MB,
            },
            status=507,
        )

    def _apply_tenant_context(self, request, tenant_slug):
        """Resolve loja, configura banco e seta thread-locals. Retorna JsonResponse de erro ou None."""
        from superadmin.models import Loja
        try:
            loja_id, db_name = self._resolve_loja_from_cache_or_db(tenant_slug)

            try:
                from core.db_config import ensure_loja_database_config
                if ensure_loja_database_config(db_name, conn_max_age=0):
                    logger.debug(f"✅ [TenantMiddleware] Banco '{db_name}' configurado")
            except Exception as db_err:
                logger.warning("TenantMiddleware: falha ao configurar banco %s, usando default: %s", db_name, db_err)
                db_name = "default"

            if db_name in settings.DATABASES:
                storage_err = self._check_storage_limit(request, db_name, tenant_slug)
                if storage_err:
                    return storage_err
                set_current_tenant_db(db_name)
            else:
                set_current_tenant_db("default")

            set_current_loja_id(loja_id)
            logger.debug(f"✅ [TenantMiddleware] Contexto setado: loja_id={loja_id}, db={getattr(_thread_locals, 'current_tenant_db', 'default')}")

        except Loja.DoesNotExist:
            if not request.path.startswith("/api/superadmin/") and not request.path.startswith("/api/suporte/"):
                logger.warning(f"⚠️ [TenantMiddleware] Loja não encontrada: slug={tenant_slug}")
            set_current_tenant_db("default")
            set_current_loja_id(None)
        except Exception as e:
            logger.exception("TenantMiddleware erro para slug=%s: %s", tenant_slug, e)
            set_current_tenant_db("default")
            set_current_loja_id(None)

    def _get_tenant_slug(self, request):
        """Extrai o slug do tenant da requisição (tenta header, ID, query, URL e subdomain).

        SEGURANÇA: Valida que o usuário autenticado pertence à loja solicitada.
        """
        return (
            self._slug_from_header(request)
            or self._slug_from_loja_id_header(request)
            or self._slug_from_query(request)
            or self._slug_from_url_path(request)
            or self._slug_from_subdomain(request)
        )

    def _slug_from_header(self, request):
        """Tenta resolver o tenant pelo header X-Tenant-Slug."""
        tenant_slug = (request.headers.get("X-Tenant-Slug") or "").strip()
        if not tenant_slug:
            return None
        if not (hasattr(request, "user") and request.user.is_authenticated):
            return tenant_slug
        if self._validate_user_owns_loja_by_slug(request, tenant_slug):
            return tenant_slug
        logger.debug(
            "[_get_tenant_slug] X-Tenant-Slug=%s rejeitado para user=%s; tentando X-Loja-ID",
            tenant_slug, getattr(request.user, "id", None),
        )
        return None

    def _slug_from_loja_id_header(self, request):
        """Tenta resolver o tenant pelo header X-Loja-ID."""
        loja_id = request.headers.get("X-Loja-ID")
        if not loja_id:
            return None
        if not (hasattr(request, "user") and request.user.is_authenticated):
            logger.debug("X-Loja-ID presente mas usuário ainda não autenticado na pilha Django (ex.: JWT)")
            return None
        try:
            from superadmin.models import Loja
            loja = Loja.objects.get(id=int(loja_id))
            if self._validate_user_owns_loja(request, loja):
                return loja.slug
            logger.warning(f"⚠️ [_get_tenant_slug] X-Loja-ID={loja_id} rejeitado para user={request.user.id}")
        except (Loja.DoesNotExist, ValueError):
            logger.warning(f"⚠️ [_get_tenant_slug] Loja id={loja_id} inválida")
        return None

    def _slug_from_query(self, request):
        """Tenta resolver o tenant pelo parâmetro de query ?tenant=."""
        tenant_slug = request.GET.get("tenant")
        if not tenant_slug:
            return None
        if hasattr(request, "user") and request.user.is_authenticated and not self._validate_user_owns_loja_by_slug(request, tenant_slug):
            return None
        return tenant_slug

    def _slug_from_url_path(self, request):
        """Tenta resolver o tenant pela URL /loja/<slug>/."""
        path_parts = request.path.split("/")
        if len(path_parts) < 3 or path_parts[1] != "loja":
            return None
        tenant_slug = path_parts[2]
        if hasattr(request, "user") and request.user.is_authenticated and not self._validate_user_owns_loja_by_slug(request, tenant_slug):
            return None
        return tenant_slug

    def _slug_from_subdomain(self, request):
        """Tenta resolver o tenant pelo subdomínio (ex: loja1.exemplo.com)."""
        host = request.get_host().split(":")[0].lower()
        railway_pub = (os.environ.get("RAILWAY_PUBLIC_DOMAIN") or "").strip().lower().split(":")[0]
        if railway_pub and host == railway_pub:
            return None
        for suf in (".up.railway.app", ".railway.app"):
            if host.endswith(suf):
                return None
        ignore_suffixes = {
            s.strip().lower()
            for s in os.environ.get("TENANT_IGNORE_SUBDOMAIN_SUFFIXES", "").split(",")
            if s.strip()
        }
        if any(host.endswith(suf) for suf in ignore_suffixes):
            return None
        parts = host.split(".")
        if len(parts) <= 2:
            return None
        tenant_slug = parts[0]
        ignore_prefixes = {
            p.strip().lower()
            for p in os.environ.get("TENANT_IGNORE_SUBDOMAIN_PREFIXES", "").split(",")
            if p.strip()
        }
        if tenant_slug in ignore_prefixes:
            return None
        if hasattr(request, "user") and request.user.is_authenticated and not self._validate_user_owns_loja_by_slug(request, tenant_slug):
            return None
        return tenant_slug

    def _validate_user_owns_loja(self, request, loja):
        """Valida que usuário autenticado pode acessar a loja."""
        if not hasattr(request, "user") or not request.user.is_authenticated:
            logger.warning("⚠️ Usuário não autenticado tentando acessar loja")
            return False

        from core.tenant_access import user_can_access_loja
        if user_can_access_loja(request.user, loja):
            return True

        logger.warning(
            "⚠️ Usuário %s (%s) não tem permissão para loja %s (owner: %s)",
            request.user.id,
            request.user.email,
            loja.slug,
            loja.owner_id,
        )
        logger.critical(
            "🚨 BLOQUEIO: Usuário %s (%s) não tem permissão para loja %s (ID: %s)",
            request.user.id,
            request.user.email,
            loja.slug,
            loja.id,
        )
        return False

    def _validate_user_owns_loja_by_slug(self, request, tenant_slug):
        """Valida que usuário autenticado é owner da loja (por slug)"""
        if not hasattr(request, "user") or not request.user.is_authenticated:
            logger.warning("⚠️ Usuário não autenticado tentando acessar loja")
            return False

        # SuperAdmin pode acessar qualquer loja
        if request.user.is_superuser:
            return True

        try:
            loja = resolve_loja_from_slug_or_cnpj(tenant_slug)

            if not loja:
                logger.warning(f"⚠️ Loja não encontrada: {tenant_slug}")
                return False

            return self._validate_user_owns_loja(request, loja)
        except Exception as e:
            logger.error(f"❌ Erro ao validar owner: {e}")
            return False
