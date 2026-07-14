"""Configuração centralizada de banco de dados para lojas (multi-tenant).

Único ponto que define ENGINE, SCHEMA_NAME e parâmetros de conexão.
Usado por: DatabaseSchemaService, TenantMiddleware, signals, backup, commands.
"""
import logging
import os
import re

import dj_database_url
from django.conf import settings

logger = logging.getLogger(__name__)

# Nome do schema PostgreSQL derivado de loja.database_name (hífen → underscore).
# Deve coincidir com a validação usada no backup (CNPJ numérico, etc.).
_LOJA_PG_SCHEMA_RE = re.compile(r"^[a-zA-Z0-9_]{1,63}$")


def _is_valid_loja_pg_schema(schema_name: str) -> bool:
    return bool(schema_name and _LOJA_PG_SCHEMA_RE.match(schema_name))


def get_loja_database_config(
    database_name: str,
    conn_max_age: int = 0,
) -> dict | None:
    """Retorna a configuração Django para banco de uma loja.

    CORREÇÃO v1007: Removido backend customizado que estava sendo ignorado.
    Volta para ENGINE padrão + OPTIONS com search_path na URL.

    Args:
        database_name: Nome do banco (ex: loja_22239255889)
        conn_max_age: Tempo em segundos para manter conexão (0=fechar ao fim, 60=manter para migrations)

    Returns:
        dict de configuração ou None se DATABASE_URL não estiver definida

    """
    if not database_name:
        return None

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.warning("get_loja_database_config: DATABASE_URL não configurada")
        return None
    if ".rlwy.net" in database_url.lower() and "sslmode=" not in database_url.lower():
        database_url += ("&" if "?" in database_url else "?") + "sslmode=require"

    if "postgres" not in database_url.lower():
        return None

    schema_name = database_name.replace("-", "_")
    if not _is_valid_loja_pg_schema(schema_name):
        logger.warning(f"get_loja_database_config: nome de schema inválido: {schema_name!r}")
        return None

    # Aspas no schema: obrigatório se o nome começa com dígito (CNPJ etc.); inofensivo nos demais.
    search_path_opt = f'-c search_path="{schema_name}",public'

    try:
        # Adicionar search_path na URL (funciona melhor que backend customizado)
        from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

        url_com_schema = database_url
        try:
            parsed = urlparse(database_url)
            if parsed.scheme and "postgres" in parsed.scheme.lower():
                query = parse_qs(parsed.query)
                query["options"] = [search_path_opt]
                new_query = urlencode(query, doseq=True)
                url_com_schema = urlunparse((
                    parsed.scheme, parsed.netloc, parsed.path,
                    parsed.params, new_query, parsed.fragment,
                ))
        except Exception as url_err:
            logger.warning(f"URL com options falhou: {url_err}")

        default_db = dj_database_url.config(default=url_com_schema, conn_max_age=0)
        opts = dict(default_db.get("OPTIONS", {}) or {})
        _h = (default_db.get("HOST") or "").lower()
        if _h.endswith(".rlwy.net"):
            opts.setdefault("sslmode", "require")

        # Garantir search_path em OPTIONS (fallback se URL não aplicou options)
        base_opt = opts.get("options", "") or ""
        if "search_path" not in base_opt:
            opts["options"] = (base_opt + " " + search_path_opt).strip()
        merged_opts = opts.get("options", "") or ""
        if "-c statement_timeout=" not in merged_opts:
            opts["options"] = (merged_opts + " -c statement_timeout=25000").strip()

        return {
            **default_db,
            "OPTIONS": opts,
            "ATOMIC_REQUESTS": False,
            "AUTOCOMMIT": True,
            "CONN_MAX_AGE": conn_max_age,
            "CONN_HEALTH_CHECKS": False,
            "TIME_ZONE": None,
        }
    except Exception as e:
        logger.warning(f"get_loja_database_config: erro ao gerar config: {e}")
        return None


def _default_tenant_conn_max_age() -> int:
    """Pool de conexões do tenant no hot path (web). Override: CONN_MAX_AGE."""
    try:
        return int(getattr(settings, "CONN_MAX_AGE", None) or os.environ.get("CONN_MAX_AGE", "120") or 120)
    except (TypeError, ValueError):
        return 120


def ensure_loja_database_config(database_name: str, conn_max_age: int | None = None) -> bool:
    """Garante que o banco da loja está em settings.DATABASES.
    Adiciona a config se ainda não existir.

    Returns:
        True se configurado com sucesso

    """
    if conn_max_age is None:
        conn_max_age = _default_tenant_conn_max_age()

    if not database_name:
        return False

    if database_name in settings.DATABASES:
        # Se a config foi criada com conn_max_age=0 (legado), promove para pool.
        cfg = settings.DATABASES[database_name]
        current = int(cfg.get("CONN_MAX_AGE") or 0)
        if conn_max_age > 0 and current == 0:
            cfg["CONN_MAX_AGE"] = conn_max_age
        return True

    config = get_loja_database_config(database_name, conn_max_age)
    if not config:
        return False

    settings.DATABASES[database_name] = config
    logger.debug(f"Banco '{database_name}' configurado em settings.DATABASES")
    return True
