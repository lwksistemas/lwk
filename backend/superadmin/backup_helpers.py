"""
Helpers e constantes para o serviço de backup de lojas.

Extraído de backup_service.py para melhor organização.
Contém: constantes, funções auxiliares e exceções de backup.
"""

import json
import re
import logging
from typing import Any, Dict, List, Optional, Tuple
from decimal import Decimal

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

# Tabelas de sistema que NUNCA entram no backup
BACKUP_SYSTEM_TABLES_EXCLUDE = {
    'django_migrations',
    'django_content_type',
    'django_session',
    'auth_permission',
    'auth_group',
}
# Prefixos de tabelas que NUNCA devem entrar no backup (superadmin, auth, django, etc.)
BACKUP_TABLE_PREFIX_BLACKLIST = (
    'auth_',
    'django_',
    'admin_',
    'superadmin_',
    'sessions_',
    'account_',
    'socialaccount_',
)
# Quando o backup usa schema PUBLIC: só exportar tabelas cujo prefixo pertence ao tipo de app da loja.
# Evita incluir cabeleireiro_*, clinica_beleza_*, crm_*, etc. no backup de uma clínica de estética.
BACKUP_TIPO_APP_TABLE_PREFIXES = {
    'clinica-de-estetica': ('stores_', 'products_', 'clinica_beleza_', 'whatsapp_', 'crm_vendas_', 'nfse_integration_'),
    'clinica-estetica': ('stores_', 'products_', 'clinica_beleza_', 'whatsapp_', 'crm_vendas_', 'nfse_integration_'),
    'clinica-da-beleza': ('stores_', 'products_', 'clinica_beleza_', 'whatsapp_', 'crm_vendas_', 'nfse_integration_'),
    'clinica-beleza': ('stores_', 'products_', 'clinica_beleza_', 'whatsapp_', 'crm_vendas_', 'nfse_integration_'),
    'e-commerce': ('stores_', 'products_', 'ecommerce_'),
    'restaurante': ('stores_', 'products_', 'restaurante_'),
    'servicos': ('stores_', 'products_', 'servicos_'),
    'cabeleireiro': ('stores_', 'products_', 'cabeleireiro_'),
    'crm-vendas': ('stores_', 'products_', 'crm_vendas_', 'nfse_integration_'),
}
# Prefixos a excluir por tipo de app (legado clinica_* removido — unificado em clinica_beleza)
BACKUP_TIPO_APP_EXCLUDED_PREFIXES: dict[str, tuple[str, ...]] = {}
# Regex para validar nome de tabela/coluna (segurança SQL: apenas alfanumérico e underscore)
BACKUP_SAFE_IDENTIFIER_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
# Schema PostgreSQL derivado de loja.database_name (valor controlado pelo backend).
# Permite nome que começa com dígito (ex.: CNPJ como schema), sempre entre aspas em SQL literal.
BACKUP_SAFE_PG_SCHEMA_RE = re.compile(r'^[a-zA-Z0-9_]{1,63}$')

# Backups antigos podem omitir estas colunas no CSV; no PG podem ser NOT NULL sem DEFAULT no servidor.
BACKUP_CRM_CONFIG_EXTRA_INT_COLUMNS = frozenset(
    {"issnet_numero_lote", "issnet_ultimo_rps_conhecido"}
)


# ---------------------------------------------------------------------------
# Exceções
# ---------------------------------------------------------------------------

class BackupExportError(Exception):
    """Exceção customizada para erros de exportação"""
    pass


class BackupImportError(Exception):
    """Exceção customizada para erros de importação"""
    pass


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------

def is_safe_pg_schema_token(name: Optional[str]) -> bool:
    return bool(name and BACKUP_SAFE_PG_SCHEMA_RE.match(name))


def _is_safe_table_name(name: str) -> bool:
    """Valida se o nome é seguro para uso em SQL (mesmo critério de DatabaseHelper.is_safe_table_name)."""
    return bool(name and BACKUP_SAFE_IDENTIFIER_RE.match(name))


_VARCHAR_LEN_RE = re.compile(
    r'^(?:character varying|varchar|character)\((\d+)\)',
    re.IGNORECASE,
)


def _truncate_backup_value_for_pg_type(val: Any, dtype: str) -> Any:
    """Trunca strings quando o tipo PG tem limite (ex.: character varying(200))."""
    if not isinstance(val, str) or not dtype:
        return val
    match = _VARCHAR_LEN_RE.match((dtype or '').strip())
    if not match:
        return val
    max_len = int(match.group(1))
    if len(val) <= max_len:
        return val
    logger.warning(
        'Backup import: truncando coluna varchar(%s) de %s para %s chars',
        max_len,
        len(val),
        max_len,
    )
    return val[:max_len]


def _zip_csv_basename_table_name(zip_inner_path: str) -> str:
    """Nome da tabela a partir do caminho do .csv dentro do ZIP (basename, sem extensão, sem BOM)."""
    base = (zip_inner_path or "").strip().lstrip("\ufeff").replace("\\", "/").rsplit("/", 1)[-1]
    if base.lower().endswith(".csv"):
        base = base[:-4]
    return base.strip()


def _ensure_crm_vendas_config_pg_int_defaults(cursor, qual: str) -> None:
    """
    Garante DEFAULT 0 no PostgreSQL para inteiros ISSNet.
    INSERT que omitir a coluna (código/CSV antigo) deixa de gerar NULL em NOT NULL.
    """
    try:
        cursor.execute(
            f"ALTER TABLE {qual} ALTER COLUMN issnet_numero_lote SET DEFAULT 0"
        )
    except Exception as e:
        logger.warning("ALTER issnet_numero_lote SET DEFAULT 0: %s", e)
    try:
        cursor.execute(
            f"ALTER TABLE {qual} ALTER COLUMN issnet_ultimo_rps_conhecido SET DEFAULT 0"
        )
    except Exception as e:
        logger.warning("ALTER issnet_ultimo_rps_conhecido SET DEFAULT 0: %s", e)


def _normalize_backup_csv_row_keys(row: Dict[str, Any]) -> Dict[str, Any]:
    """Remove BOM e espaços nos nomes de colunas do CSV (DictReader)."""
    if not row:
        return row
    out: Dict[str, Any] = {}
    for k, v in row.items():
        if k is None:
            continue
        nk = str(k).replace("\ufeff", "").strip()
        if nk:
            out[nk] = v
    return out


def _is_crm_issnet_int_col(name: str) -> bool:
    n = (name or "").strip().lower()
    return n in ("issnet_numero_lote", "issnet_ultimo_rps_conhecido")


def _coerce_int_or_zero(val: Any) -> int:
    """Converte valor para inteiro, retornando 0 em caso de falha (NULL, string inválida, etc.)."""
    if val is None or val == "":
        return 0
    if isinstance(val, str):
        s = val.strip().lower()
        if s in ("", "null", "none", "nan"):
            return 0
        try:
            return int(float(val.strip()))
        except ValueError:
            return 0
    try:
        return int(val)
    except (TypeError, ValueError):
        return 0


def _backup_finalize_crm_config_row_values(
    cols_for_insert: List[str], values: List[Any]
) -> List[Any]:
    """Garante inteiros NOT NULL do CRM mesmo com CSV/col_info inconsistentes."""
    out: List[Any] = []
    for col, val in zip(cols_for_insert, values):
        col_n = (col or "").strip().lower()
        if col_n in ("issnet_numero_lote", "issnet_ultimo_rps_conhecido"):
            out.append(_coerce_int_or_zero(val))
        else:
            out.append(val)
    return out


def _sanitize_pg_table_key(name: str) -> str:
    """Remove BOM e caracteres invisíveis comuns em nomes vindos do ZIP."""
    s = (name or "").strip().lstrip("\ufeff")
    for z in ("\u200b", "\u200c", "\u200d", "\u2060"):
        s = s.replace(z, "")
    return s.strip()


def _parse_pg_qualified_table(qual: str) -> Tuple[Optional[str], str]:
    """
    Extrai (schema, tabela) de "schema"."tabela".
    Se não estiver qualificado, retorna (None, nome_da_tabela).
    """
    q = (qual or "").strip()
    m = re.match(r'^"([^"]+)"\."([^"]+)"$', q)
    if m:
        return m.group(1), m.group(2)
    inner = q.strip('"')
    if inner and BACKUP_SAFE_IDENTIFIER_RE.match(inner):
        return None, inner
    return None, "crm_vendas_config"


def _connection_is_postgresql(conn) -> bool:
    if getattr(conn, "vendor", None) == "postgresql":
        return True
    eng = (conn.settings_dict.get("ENGINE") or "").lower()
    return "postgresql" in eng


def _resolve_visible_pg_schema_for_table(cur, table_name: str) -> Optional[str]:
    """
    Primeiro schema no search_path onde existe uma relação visível com relname = table_name.
    Alinha metadados com INSERT não qualificado em PostgreSQL.
    """
    if not _is_safe_table_name(table_name):
        return None
    try:
        cur.execute(
            """
            SELECT n.nspname
            FROM unnest(current_schemas(true)) WITH ORDINALITY AS sp(schema_name, ord)
            INNER JOIN pg_catalog.pg_namespace n ON n.nspname = sp.schema_name
            INNER JOIN pg_catalog.pg_class c ON c.relnamespace = n.oid
                AND c.relname = %s AND c.relkind IN ('r', 'p')
            ORDER BY sp.ord ASC
            LIMIT 1
            """,
            [table_name],
        )
        r = cur.fetchone()
        if r and r[0] and is_safe_pg_schema_token(r[0]):
            return r[0]
    except Exception as ex:
        logger.warning("resolve_visible_schema %s: %s", table_name, ex)
    return None


def _fetch_crm_vendas_config_pg_colrows(
    cur, qual: str, pg_schema: str
) -> List[Tuple[Any, Any, Any]]:
    """
    Colunas da tabela física em ordem: (nome, is_nullable YES/NO, tipo/format_type).
    Prioriza o schema do qual(...) do INSERT (evita omitir NOT NULL quando pg_schema ≠ schema real).
    """
    q_schema, q_table = _parse_pg_qualified_table(qual)
    if not BACKUP_SAFE_IDENTIFIER_RE.match(q_table):
        q_table = "crm_vendas_config"
    candidates: List[str] = []
    # INSERT sem schema: mesma tabela que o PostgreSQL resolve via search_path
    if q_schema is None:
        vis = _resolve_visible_pg_schema_for_table(cur, q_table)
        if vis and vis not in candidates:
            candidates.append(vis)
    for s in (q_schema, pg_schema):
        if s and is_safe_pg_schema_token(s) and s not in candidates:
            candidates.append(s)
    try:
        cur.execute("SELECT current_schema()")
        cr = cur.fetchone()
        if cr and cr[0] and is_safe_pg_schema_token(cr[0]) and cr[0] not in candidates:
            candidates.append(cr[0])
    except Exception:
        pass
    if q_schema is None and "public" not in candidates:
        candidates.append("public")

    for schema_try in candidates:
        cur.execute(
            """
            SELECT a.attname,
                   CASE WHEN a.attnotnull THEN 'NO' ELSE 'YES' END,
                   pg_catalog.format_type(a.atttypid, a.atttypmod)
            FROM pg_catalog.pg_attribute a
            INNER JOIN pg_catalog.pg_class c ON a.attrelid = c.oid
            INNER JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
            WHERE n.nspname = %s AND c.relname = %s
              AND a.attnum > 0 AND NOT a.attisdropped
            ORDER BY a.attnum
            """,
            [schema_try, q_table],
        )
        found = cur.fetchall()
        if found:
            return list(found)

    for schema_try in candidates:
        cur.execute(
            """
            SELECT column_name, is_nullable, data_type
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
            """,
            [schema_try, q_table],
        )
        found = cur.fetchall()
        if found:
            return list(found)
    return []


def _import_crm_vendas_config_via_model(
    loja,
    rows: List[Dict[str, Any]],
    qual: str,
    using: str,
    pg_schema: str,
) -> None:
    """
    Importa crm_vendas_config com INSERT explícito no schema da loja (qual).

    Usa a ordem e o conjunto de colunas da tabela real no PostgreSQL
    (information_schema), para não omitir colunas NOT NULL que existam na BD
    mas não no kwargs do modelo.
    """
    from django.db import connections
    from django.db import models as dm
    from django.utils import timezone
    from django.utils.dateparse import parse_datetime
    from crm_vendas.models_config import CRMConfig

    conn = connections[using]

    def as_int(raw: Any, default: int = 0) -> int:
        if raw is None:
            return default
        if isinstance(raw, str):
            s = raw.strip().lower()
            if s in ("", "null", "none", "nan"):
                return default
            try:
                return int(float(s))
            except ValueError:
                return default
        try:
            return int(raw)
        except (TypeError, ValueError):
            return default

    def as_dec(raw: Any, default: Decimal) -> Decimal:
        if raw is None or (isinstance(raw, str) and not str(raw).strip()):
            return default
        try:
            return Decimal(str(raw).strip())
        except Exception:
            return default

    def as_bool(raw: Any, default: bool = False) -> bool:
        if raw is None or raw == "":
            return default
        if isinstance(raw, bool):
            return raw
        return str(raw).strip().lower() in ("1", "t", "true", "yes")

    def as_json(raw: Any, default: Any) -> Any:
        if raw is None or (isinstance(raw, str) and not str(raw).strip()):
            return default
        if isinstance(raw, (list, dict)):
            return raw
        return json.loads(raw)

    def as_bytes(raw: Any) -> Optional[bytes]:
        if raw is None or (isinstance(raw, str) and not str(raw).strip()):
            return None
        s = str(raw).strip()
        if s.startswith("\\x") or s.startswith("\\\\x"):
            hx = s.replace("\\\\x", "\\x")
            if hx.startswith("\\x"):
                hx = hx[2:]
            try:
                return bytes.fromhex(hx)
            except ValueError:
                return None
        try:
            return bytes.fromhex(s)
        except ValueError:
            return None

    is_sqlite = conn.settings_dict.get("ENGINE", "").endswith("sqlite3")
    with conn.cursor() as cur:
        if not is_sqlite and _connection_is_postgresql(conn):
            _ensure_crm_vendas_config_pg_int_defaults(cur, qual)
        cur.execute(f"DELETE FROM {qual}")
        static_colrows: List[Tuple[Any, Any, Any]] = []
        if not is_sqlite and _connection_is_postgresql(conn):
            static_colrows = _fetch_crm_vendas_config_pg_colrows(cur, qual, pg_schema)
            if not static_colrows:
                logger.warning(
                    "crm_vendas_config: não foi possível listar colunas via pg_catalog/"
                    "information_schema (qual=%r pg_schema=%r). Usando fallback pelo modelo.",
                    qual,
                    pg_schema,
                )

        for row in rows:
            row = _normalize_backup_csv_row_keys(row)
            kwargs: Dict[str, Any] = {"loja_id": loja.id}
            for field in CRMConfig._meta.local_concrete_fields:
                att = field.attname
                if att == "loja_id":
                    continue
                if getattr(field, "auto_now", False) or getattr(field, "auto_now_add", False):
                    raw_dt = row.get(att)
                    if raw_dt:
                        parsed = parse_datetime(str(raw_dt))
                        if parsed is not None:
                            kwargs[att] = parsed
                    continue

                if isinstance(field, dm.AutoField):
                    raw_id = row.get(att)
                    if raw_id is not None and str(raw_id).strip() != "":
                        kwargs[att] = as_int(raw_id, 0)
                    continue

                raw = row.get(att)
                if isinstance(field, dm.BinaryField):
                    if raw is None or (isinstance(raw, str) and not str(raw).strip()):
                        raw = row.get("issnet_certificado_binary")
                    kwargs[att] = as_bytes(raw)
                    continue

                if isinstance(field, dm.JSONField):
                    kwargs[att] = as_json(raw, field.get_default())
                    continue

                if isinstance(field, dm.BooleanField):
                    d = field.get_default() if field.has_default() else False
                    if not isinstance(d, bool):
                        d = bool(d)
                    kwargs[att] = as_bool(raw, d)
                    continue

                if isinstance(field, dm.DecimalField):
                    d0 = field.get_default() if field.has_default() else Decimal("0")
                    if not isinstance(d0, Decimal):
                        d0 = Decimal(str(d0))
                    kwargs[att] = as_dec(raw, d0)
                    continue

                if isinstance(field, dm.DateTimeField):
                    if raw is None or (isinstance(raw, str) and not str(raw).strip()):
                        if field.null:
                            kwargs[att] = None
                        continue
                    parsed = parse_datetime(str(raw))
                    kwargs[att] = parsed if parsed is not None else None
                    continue

                if isinstance(
                    field, (dm.IntegerField, dm.BigIntegerField, dm.SmallIntegerField)
                ):
                    d = 0
                    if field.has_default():
                        try:
                            d = int(field.get_default())
                        except (TypeError, ValueError):
                            d = 0
                    kwargs[att] = as_int(raw, d)
                    continue

                if raw is None:
                    kwargs[att] = (
                        field.get_default() if field.has_default() else ""
                    )
                else:
                    kwargs[att] = str(raw)

            kwargs["issnet_numero_lote"] = as_int(row.get("issnet_numero_lote"), 0)
            kwargs["issnet_ultimo_rps_conhecido"] = as_int(
                row.get("issnet_ultimo_rps_conhecido"), 0
            )
            kwargs["loja_id"] = loja.id

            def _value_for_physical_column(
                col_name: str, nullable: bool, pg_dtype: str
            ) -> Any:
                dt = (pg_dtype or "").lower()
                raw_kw = kwargs.get(col_name)
                if col_name == "id" and raw_kw is None:
                    return None
                if _is_crm_issnet_int_col(col_name):
                    return as_int(raw_kw if raw_kw is not None else row.get(col_name), 0)
                if raw_kw is not None:
                    v = raw_kw
                    try:
                        finfo = CRMConfig._meta.get_field(col_name)
                    except Exception:
                        finfo = None
                    if (
                        finfo is not None
                        and isinstance(finfo, dm.JSONField)
                        and not isinstance(v, (str, bytes, int, float, bool))
                    ):
                        return json.dumps(v, default=str)
                    return v
                if nullable:
                    return None
                if "char" in dt or dt == "text":
                    return ""
                if dt in ("integer", "bigint", "smallint"):
                    return 0
                if dt == "boolean":
                    return False
                if dt.startswith("numeric") or dt == "decimal":
                    return Decimal("0")
                if "timestamp" in dt or dt == "date":
                    return timezone.now()
                if dt == "bytea":
                    return None
                return None

            colrows = static_colrows

            if colrows:
                ordered_cols = []
                values_out = []
                for col_name, is_nullable, pg_dtype in colrows:
                    col_name = (col_name or "").strip()
                    nullable = is_nullable == "YES"
                    v = _value_for_physical_column(col_name, nullable, pg_dtype)
                    if col_name == "id" and v is None:
                        continue
                    ordered_cols.append(col_name)
                    values_out.append(v)
            else:
                ordered_cols = [
                    f.attname
                    for f in CRMConfig._meta.local_concrete_fields
                    if f.attname in kwargs
                    and BACKUP_SAFE_IDENTIFIER_RE.match(f.attname)
                ]
                values_out = []
                for c in ordered_cols:
                    v = kwargs[c]
                    try:
                        finfo = CRMConfig._meta.get_field(c)
                    except Exception:
                        finfo = None
                    if (
                        finfo is not None
                        and isinstance(finfo, dm.JSONField)
                        and v is not None
                        and not isinstance(v, (str, bytes, int, float, bool))
                    ):
                        values_out.append(json.dumps(v, default=str))
                    else:
                        values_out.append(v)

            # Metadados podem omitir colunas (schema errado, view antiga, etc.): o INSERT sem a coluna
            # NOT NULL gera NULL no servidor — reforçar as duas colunas críticas do CRM/NFS-e.
            for extra_col in BACKUP_CRM_CONFIG_EXTRA_INT_COLUMNS:
                if not any((c or "").strip().lower() == extra_col for c in ordered_cols):
                    ordered_cols.append(extra_col)
                    values_out.append(as_int(row.get(extra_col), 0))
                    logger.warning(
                        "crm_vendas_config: coluna %s ausente na listagem física; "
                        "incluída no INSERT com 0 (qual=%r)",
                        extra_col,
                        qual,
                    )

            qcols = ", ".join(f'"{c}"' for c in ordered_cols)
            if not ordered_cols:
                raise BackupImportError(
                    "crm_vendas_config: nenhuma coluna para INSERT (schema inesperado)"
                )

            for must in BACKUP_CRM_CONFIG_EXTRA_INT_COLUMNS:
                if not any((c or "").strip().lower() == must for c in ordered_cols):
                    raise BackupImportError(
                        f"crm_vendas_config: coluna obrigatória {must!r} ausente após merge; "
                        f"qual={qual!r} colunas={ordered_cols[:25]}..."
                    )

            for i, c in enumerate(ordered_cols):
                if _is_crm_issnet_int_col(c):
                    values_out[i] = as_int(values_out[i], 0)

            if is_sqlite:
                ph = ", ".join(["%s"] * len(ordered_cols))
                exec_params: List[Any] = list(values_out)
            else:
                ph_parts: List[str] = []
                exec_params = []
                for i, c in enumerate(ordered_cols):
                    v = values_out[i]
                    if _is_crm_issnet_int_col(c):
                        ival = as_int(v, 0)
                        # Inteiro literal no SQL: evita NULL via adaptador/psycopg em colunas NOT NULL.
                        ph_parts.append(str(ival))
                    else:
                        ph_parts.append("%s")
                        exec_params.append(v)
                ph = ", ".join(ph_parts)
            sql = f"INSERT INTO {qual} ({qcols}) VALUES ({ph})"
            cur.execute(sql, exec_params)
