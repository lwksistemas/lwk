"""
Serviço de Backup de Lojas - v800

Responsabilidades:
- Exportar dados de lojas em formato CSV
- Importar dados de backups
- Enviar backups por email
- Gerenciar arquivos de backup

Boas práticas aplicadas:
- Single Responsibility Principle
- Dependency Injection
- Error Handling robusto
- Logging detalhado
- Type hints
"""

import csv
import json
import zipfile
import io
import os
import re
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from decimal import Decimal

from django.db import connections, transaction
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# Constantes (evitar magic numbers e listas soltas no código)
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
    'clinica-de-estetica': ('stores_', 'products_', 'clinica_'),
    'clinica-estetica': ('stores_', 'products_', 'clinica_'),
    'clinica-da-beleza': ('stores_', 'products_', 'clinica_beleza_', 'whatsapp_'),
    'e-commerce': ('stores_', 'products_', 'ecommerce_'),
    'restaurante': ('stores_', 'products_', 'restaurante_'),
    'servicos': ('stores_', 'products_', 'servicos_'),
    'cabeleireiro': ('stores_', 'products_', 'cabeleireiro_'),
    'crm-vendas': ('stores_', 'products_', 'crm_vendas_', 'nfse_integration_'),
}
# Prefixos a excluir por tipo de app (ex.: clinica_beleza_ não é da clínica de estética)
BACKUP_TIPO_APP_EXCLUDED_PREFIXES = {
    'clinica-de-estetica': ('clinica_beleza_',),
    'clinica-estetica': ('clinica_beleza_',),
}
# Regex para validar nome de tabela/coluna (segurança SQL: apenas alfanumérico e underscore)
BACKUP_SAFE_IDENTIFIER_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
# Schema PostgreSQL derivado de loja.database_name (valor controlado pelo backend).
# Permite nome que começa com dígito (ex.: CNPJ como schema), sempre entre aspas em SQL literal.
BACKUP_SAFE_PG_SCHEMA_RE = re.compile(r'^[a-zA-Z0-9_]{1,63}$')


def is_safe_pg_schema_token(name: Optional[str]) -> bool:
    return bool(name and BACKUP_SAFE_PG_SCHEMA_RE.match(name))
# Backups antigos podem omitir estas colunas no CSV; no PG podem ser NOT NULL sem DEFAULT no servidor.
BACKUP_CRM_CONFIG_EXTRA_INT_COLUMNS = frozenset(
    {"issnet_numero_lote", "issnet_ultimo_rps_conhecido"}
)


def _backup_finalize_crm_config_row_values(
    cols_for_insert: List[str], values: List[Any]
) -> List[Any]:
    """Garante inteiros NOT NULL do CRM mesmo com CSV/col_info inconsistentes."""
    out: List[Any] = []
    for col, val in zip(cols_for_insert, values):
        if col == "issnet_numero_lote":
            if val is None or val == "":
                out.append(0)
            elif isinstance(val, str):
                s = val.strip().lower()
                if s in ("", "null", "none", "nan"):
                    out.append(0)
                else:
                    try:
                        out.append(int(float(val.strip())))
                    except ValueError:
                        out.append(0)
            else:
                try:
                    out.append(int(val))
                except (TypeError, ValueError):
                    out.append(0)
        elif col == "issnet_ultimo_rps_conhecido":
            if val is None or val == "":
                out.append(0)
            elif isinstance(val, str):
                s = val.strip().lower()
                if s in ("", "null", "none", "nan"):
                    out.append(0)
                else:
                    try:
                        out.append(int(float(val.strip())))
                    except ValueError:
                        out.append(0)
            else:
                try:
                    out.append(int(val))
                except (TypeError, ValueError):
                    out.append(0)
        else:
            out.append(val)
    return out


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
    if not DatabaseHelper.is_safe_table_name(table_name):
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
                if col_name in ("issnet_numero_lote", "issnet_ultimo_rps_conhecido"):
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
                if extra_col not in ordered_cols:
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

            for i, c in enumerate(ordered_cols):
                if c in BACKUP_CRM_CONFIG_EXTRA_INT_COLUMNS:
                    values_out[i] = as_int(values_out[i], 0)

            if is_sqlite:
                ph = ", ".join(["%s"] * len(ordered_cols))
                exec_params: List[Any] = list(values_out)
            else:
                ph_parts: List[str] = []
                exec_params = []
                for i, c in enumerate(ordered_cols):
                    v = values_out[i]
                    if c in BACKUP_CRM_CONFIG_EXTRA_INT_COLUMNS:
                        ph_parts.append("COALESCE(%s::integer, 0)")
                        exec_params.append(v)
                    else:
                        ph_parts.append("%s")
                        exec_params.append(v)
                ph = ", ".join(ph_parts)
            sql = f"INSERT INTO {qual} ({qcols}) VALUES ({ph})"
            cur.execute(sql, exec_params)


class BackupExportError(Exception):
    """Exceção customizada para erros de exportação"""
    pass


class BackupImportError(Exception):
    """Exceção customizada para erros de importação"""
    pass



class TabelaConfig:
    """
    Configuração de uma tabela para backup.
    
    Encapsula informações sobre como exportar/importar cada tabela.
    """
    
    def __init__(
        self,
        nome: str,
        ordem_exportacao: int = 100,
        ordem_importacao: int = 100,
        incluir_imagens: bool = False
    ):
        self.nome = nome
        self.ordem_exportacao = ordem_exportacao
        self.ordem_importacao = ordem_importacao
        self.incluir_imagens = incluir_imagens
    
    def __repr__(self):
        return f"TabelaConfig({self.nome})"


class BackupConfig:
    """
    Configuração centralizada de tabelas para backup.
    
    Define quais tabelas devem ser incluídas e em qual ordem.
    Facilita manutenção e extensão do sistema.
    """
    
    # Tabelas principais (ordem de exportação/importação é importante)
    TABELAS = [
        # Cadastros básicos (sem dependências)
        TabelaConfig('categorias', ordem_exportacao=1, ordem_importacao=1),
        TabelaConfig('fornecedores', ordem_exportacao=2, ordem_importacao=2),
        TabelaConfig('clientes', ordem_exportacao=3, ordem_importacao=3),
        TabelaConfig('profissionais', ordem_exportacao=4, ordem_importacao=4),
        
        # Produtos e serviços (dependem de categorias)
        TabelaConfig('produtos', ordem_exportacao=10, ordem_importacao=10),
        TabelaConfig('servicos', ordem_exportacao=11, ordem_importacao=11),
        
        # Estoque (depende de produtos)
        TabelaConfig('estoque', ordem_exportacao=20, ordem_importacao=20),
        TabelaConfig('movimentacoes_estoque', ordem_exportacao=21, ordem_importacao=21),
        
        # Agendamentos (depende de profissionais e serviços)
        TabelaConfig('agendamentos', ordem_exportacao=30, ordem_importacao=30),
        
        # Vendas (depende de clientes e produtos)
        TabelaConfig('vendas', ordem_exportacao=40, ordem_importacao=40),
        TabelaConfig('itens_venda', ordem_exportacao=41, ordem_importacao=41),
        TabelaConfig('pagamentos', ordem_exportacao=42, ordem_importacao=42),
        # CRM Vendas (ordem: vendedor antes de conta/lead; conta antes de lead/contato; lead antes de oportunidade/atividade)
        TabelaConfig('crm_vendas_vendedor', ordem_exportacao=100, ordem_importacao=100),
        TabelaConfig('crm_vendas_conta', ordem_exportacao=101, ordem_importacao=101),
        TabelaConfig('crm_vendas_lead', ordem_exportacao=102, ordem_importacao=102),
        TabelaConfig('crm_vendas_contato', ordem_exportacao=103, ordem_importacao=103),
        TabelaConfig('crm_vendas_oportunidade', ordem_exportacao=104, ordem_importacao=104),
        TabelaConfig('crm_vendas_atividade', ordem_exportacao=105, ordem_importacao=105),
        TabelaConfig('crm_vendas_config', ordem_exportacao=106, ordem_importacao=106),
        TabelaConfig('crm_vendas_produto_servico', ordem_exportacao=107, ordem_importacao=107),
        TabelaConfig('crm_vendas_oportunidade_item', ordem_exportacao=108, ordem_importacao=108),
        TabelaConfig('crm_vendas_proposta', ordem_exportacao=109, ordem_importacao=109),
        TabelaConfig('crm_vendas_contrato', ordem_exportacao=110, ordem_importacao=110),
        TabelaConfig('nfse_integration_nfse', ordem_exportacao=111, ordem_importacao=111),
    ]
    
    @classmethod
    def get_tabelas_ordenadas_exportacao(cls) -> List[TabelaConfig]:
        """Retorna tabelas ordenadas para exportação"""
        return sorted(cls.TABELAS, key=lambda t: t.ordem_exportacao)
    
    @classmethod
    def get_tabelas_ordenadas_importacao(cls) -> List[TabelaConfig]:
        """Retorna tabelas ordenadas para importação"""
        return sorted(cls.TABELAS, key=lambda t: t.ordem_importacao)
    
    @classmethod
    def get_nomes_tabelas(cls) -> List[str]:
        """Retorna lista de nomes de tabelas"""
        return [t.nome for t in cls.TABELAS]



class DatabaseHelper:
    """
    Helper para operações de banco de dados.
    
    Encapsula lógica de conexão e queries ao banco isolado da loja.
    No PostgreSQL usa schema explícito (database_name com - trocado por _) para
    não depender de search_path no one-off dyno do Scheduler.
    """
    
    def __init__(self, database_name: str):
        self.database_name = database_name
        # Schema PostgreSQL = alias com hífens trocados por underscore (ex: loja_clinica_vida_5889)
        self._pg_schema = (database_name or '').replace('-', '_') if database_name else ''
    
    def get_connection(self):
        """Retorna conexão com o banco da loja"""
        return connections[self.database_name]
    
    def _is_sqlite(self) -> bool:
        """Detecta se o backend é SQLite"""
        conn = self.get_connection()
        return conn.settings_dict.get('ENGINE', '').endswith('sqlite3')
    
    def _qualified_table(self, table_name: str) -> str:
        """Retorna nome qualificado para PostgreSQL (schema.tabela) ou só tabela para SQLite."""
        if self._is_sqlite() or not self._pg_schema or not self.is_safe_table_name(table_name):
            return table_name
        if not (self._pg_schema and is_safe_pg_schema_token(self._pg_schema)):
            return table_name
        return f'"{self._pg_schema}"."{table_name}"'
    
    def qualified_table_name(self, table_name: str) -> str:
        """Nome da tabela qualificado com schema (PostgreSQL) ou só o nome (SQLite). Uso em SQL."""
        return self._qualified_table(table_name)
    
    def ensure_pg_schema_exists(self) -> bool:
        """Cria o schema no PostgreSQL se não existir (usa a conexão da loja). Retorna True se OK."""
        if self._is_sqlite() or not self._pg_schema or not is_safe_pg_schema_token(self._pg_schema):
            return True
        try:
            with self.get_connection().cursor() as cursor:
                cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{self._pg_schema}"')
            logger.info(f"Schema PostgreSQL '{self._pg_schema}' garantido (CREATE IF NOT EXISTS)")
            return True
        except Exception as e:
            logger.warning(f"Falha ao criar schema '{self._pg_schema}': {e}")
            return False

    def _get_current_schema_pg(self) -> Optional[str]:
        """Retorna o schema atual da conexão (PostgreSQL). Útil quando search_path está setado."""
        if self._is_sqlite():
            return None
        try:
            with self.get_connection().cursor() as cursor:
                cursor.execute("SELECT current_schema()")
                row = cursor.fetchone()
                return row[0] if row else None
        except Exception as e:
            logger.warning(f"Erro ao obter current_schema: {e}")
            return None

    def get_all_table_names(self) -> List[str]:
        """Lista todas as tabelas do schema/banco (PostgreSQL ou SQLite). Exclui django_migrations.
        Em PostgreSQL: usa current_schema() da conexão (mesmo critério do ORM) para evitar ZIP vazio."""
        tables = []
        with self.get_connection().cursor() as cursor:
            if self._is_sqlite():
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
                )
                tables = [row[0] for row in cursor.fetchall()]
            else:
                # Usar current_schema() para listar tabelas (mesma conexão que o ORM usa no request)
                current = self._get_current_schema_pg()
                if current:
                    self._pg_schema = current
                cursor.execute(
                    """
                    SELECT tablename FROM pg_tables
                    WHERE schemaname = current_schema()
                    ORDER BY tablename
                    """
                )
                tables = [row[0] for row in cursor.fetchall()]
                if tables:
                    logger.info(f"Backup: {len(tables)} tabela(s) em current_schema()='{self._pg_schema}'")
                if not tables:
                    cursor.execute(
                        """
                        SELECT table_name FROM information_schema.tables
                        WHERE table_schema = %s AND table_type = 'BASE TABLE'
                        ORDER BY table_name
                        """,
                        [self._pg_schema]
                    )
                    tables = [row[0] for row in cursor.fetchall()]
                # Fallback: se o schema da loja está vazio, listar do public (ORM pode estar usando public)
                if not tables and self._pg_schema and self._pg_schema != 'public':
                    cursor.execute(
                        """
                        SELECT tablename FROM pg_tables
                        WHERE schemaname = 'public'
                        ORDER BY tablename
                        """
                    )
                    tables = [row[0] for row in cursor.fetchall()]
                    if tables:
                        self._pg_schema = 'public'
                        logger.info(
                            f"Backup: 0 tabelas no schema nominal; usando schema 'public' ({len(tables)} tabela(s))"
                        )
                if not tables:
                    current = self._get_current_schema_pg()
                    logger.warning(
                        f"Backup: 0 tabelas em current_schema e em schema '{self._pg_schema}'; "
                        f"current_schema()='{current}'"
                    )
        # Excluir tabelas de sistema e prefixos proibidos (superadmin, auth, django, etc.)
        def _allow_table(name: str) -> bool:
            if name in BACKUP_SYSTEM_TABLES_EXCLUDE:
                return False
            return not any(name.startswith(prefix) for prefix in BACKUP_TABLE_PREFIX_BLACKLIST)
        return [t for t in tables if _allow_table(t)]
    
    @staticmethod
    def is_safe_table_name(name: str) -> bool:
        """Valida se o nome é seguro para uso em SQL (evita injection)."""
        return bool(name and BACKUP_SAFE_IDENTIFIER_RE.match(name))
    
    def table_exists(self, table_name: str) -> bool:
        """Verifica se uma tabela existe no banco"""
        if not self.is_safe_table_name(table_name):
            logger.warning(f"Nome de tabela inválido (segurança): {table_name!r}")
            return False
        try:
            with self.get_connection().cursor() as cursor:
                if self._is_sqlite():
                    cursor.execute(
                        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=%s",
                        [table_name]
                    )
                else:
                    if not is_safe_pg_schema_token(self._pg_schema):
                        return False
                    cursor.execute(
                        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = %s AND table_name = %s)",
                        [self._pg_schema, table_name]
                    )
                row = cursor.fetchone()
                if self._is_sqlite():
                    return row is not None
                return bool(row[0]) if row else False
        except Exception as e:
            logger.warning(f"Erro ao verificar existência da tabela {table_name}: {e}")
            return False
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """Retorna lista de colunas de uma tabela"""
        if not self.is_safe_table_name(table_name):
            return []
        with self.get_connection().cursor() as cursor:
            if self._is_sqlite():
                cursor.execute(f"PRAGMA table_info({table_name})")
                return [row[1] for row in cursor.fetchall()]
            if not is_safe_pg_schema_token(self._pg_schema):
                return []
            cursor.execute(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
                """,
                [self._pg_schema, table_name]
            )
            return [row[0] for row in cursor.fetchall()]

    def _fetch_pg_attribute_meta(
        self, schema: str, table_name: str
    ) -> Tuple[List[str], Dict[str, Tuple[bool, str]]]:
        """Uma query: nomes de colunas (ordem física) + (aceita NULL?, format_type)."""
        if not self.is_safe_table_name(table_name) or not is_safe_pg_schema_token(schema):
            return [], {}
        try:
            with self.get_connection().cursor() as cursor:
                cursor.execute(
                    """
                    SELECT a.attname,
                           a.attnotnull,
                           pg_catalog.format_type(a.atttypid, a.atttypmod)
                    FROM pg_catalog.pg_attribute a
                    INNER JOIN pg_catalog.pg_class c ON a.attrelid = c.oid
                    INNER JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
                    WHERE n.nspname = %s AND c.relname = %s
                      AND a.attnum > 0 AND NOT a.attisdropped
                    ORDER BY a.attnum
                    """,
                    [schema, table_name],
                )
                rows = cursor.fetchall()
                cols = [r[0] for r in rows]
                # attnotnull True = NOT NULL → primeiro elemento False = não aceita NULL (como is_nullable NO)
                meta = {r[0]: (not r[1], r[2] or "") for r in rows}
                return cols, meta
        except Exception as e:
            logger.warning("pg_catalog meta %s.%s: %s", schema, table_name, e)
            return [], {}

    def get_pg_table_meta_for_backup(
        self, table_name: str
    ) -> Tuple[List[str], Dict[str, Tuple[bool, str]]]:
        """Colunas + tipos via pg_attribute; usa current_schema() e o schema nominal da loja."""
        if self._is_sqlite() or not self.is_safe_table_name(table_name):
            return [], {}
        schemas: List[str] = []
        try:
            with self.get_connection().cursor() as cur:
                cur.execute("SELECT current_schema()")
                r = cur.fetchone()
                if r and r[0] and is_safe_pg_schema_token(r[0]):
                    schemas.append(r[0])
        except Exception as e:
            logger.warning("current_schema() falhou: %s", e)
        if (
            self._pg_schema
            and is_safe_pg_schema_token(self._pg_schema)
            and self._pg_schema not in schemas
        ):
            schemas.append(self._pg_schema)
        for sch in schemas:
            if not is_safe_pg_schema_token(sch):
                continue
            cols, meta = self._fetch_pg_attribute_meta(sch, table_name)
            if cols:
                return cols, meta
        return [], {}

    def get_columns_nullable_and_type(self, table_name: str) -> Dict[str, Tuple[bool, str]]:
        """Retorna dict col -> (is_nullable, data_type) para colunas da tabela."""
        if not self.is_safe_table_name(table_name):
            return {}
        with self.get_connection().cursor() as cursor:
            if self._is_sqlite():
                cursor.execute(f"PRAGMA table_info({table_name})")
                return {row[1]: (row[3] == 0, row[2] or '') for row in cursor.fetchall()}
            if not is_safe_pg_schema_token(self._pg_schema):
                return {}
            cursor.execute(
                """
                SELECT column_name, is_nullable, data_type
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
                """,
                [self._pg_schema, table_name]
            )
            return {row[0]: (row[1] == 'YES', row[2] or '') for row in cursor.fetchall()}
    
    def count_records(self, table_name: str) -> int:
        """Conta registros em uma tabela"""
        if not self.is_safe_table_name(table_name):
            return 0
        qual = self._qualified_table(table_name)
        with self.get_connection().cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {qual}")
            return cursor.fetchone()[0]
    
    def _table_has_loja_id(self, table_name: str) -> bool:
        """Verifica se a tabela possui coluna loja_id (isolamento por loja)."""
        if not self.is_safe_table_name(table_name):
            return False
        columns = self.get_table_columns(table_name)
        return 'loja_id' in columns

    def fetch_all_records(
        self, table_name: str, loja_id: Optional[int] = None
    ) -> Tuple[List[str], List[tuple]]:
        """
        Busca todos os registros de uma tabela.
        Se loja_id for informado e a tabela tiver coluna loja_id, filtra apenas
        os registros daquela loja (backup com cadastros só da loja individual).

        Returns:
            Tuple com (colunas, registros)
        """
        if not self.is_safe_table_name(table_name):
            return [], []
        columns = self.get_table_columns(table_name)
        qual = self._qualified_table(table_name)
        use_loja_filter = (
            loja_id is not None
            and self._table_has_loja_id(table_name)
        )
        with self.get_connection().cursor() as cursor:
            if use_loja_filter:
                cursor.execute(
                    f'SELECT * FROM {qual} WHERE loja_id = %s',
                    [loja_id],
                )
            else:
                cursor.execute(f"SELECT * FROM {qual}")
            records = cursor.fetchall()
        return columns, records



class CSVExporter:
    """
    Exportador de dados para CSV.
    
    Responsável por converter dados do banco em arquivos CSV.
    """
    
    @staticmethod
    def export_table_to_csv(
        table_name: str,
        columns: List[str],
        records: List[tuple]
    ) -> bytes:
        """
        Exporta uma tabela para CSV em memória.
        
        Args:
            table_name: Nome da tabela
            columns: Lista de colunas
            records: Lista de registros
        
        Returns:
            bytes: Conteúdo do CSV em bytes
        """
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        
        # Escrever cabeçalho
        writer.writerow(columns)
        
        # Escrever registros
        for record in records:
            # Converter valores para string, tratando None e tipos especiais
            row = [CSVExporter._format_value(val) for val in record]
            writer.writerow(row)
        
        # Converter para bytes
        csv_content = output.getvalue()
        output.close()
        
        return csv_content.encode('utf-8')
    
    @staticmethod
    def _format_value(value):
        """Formata um valor para CSV"""
        if value is None:
            return ''
        if isinstance(value, (datetime, timezone.datetime)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, bool):
            return '1' if value else '0'
        return str(value)


class ZipBuilder:
    """
    Construtor de arquivos ZIP.
    
    Responsável por criar o arquivo ZIP com todos os CSVs.
    """
    
    def __init__(self):
        self.zip_buffer = io.BytesIO()
        self.zip_file = zipfile.ZipFile(
            self.zip_buffer,
            'w',
            zipfile.ZIP_DEFLATED,
            compresslevel=9
        )
    
    def add_csv(self, filename: str, csv_content: bytes):
        """Adiciona um arquivo CSV ao ZIP"""
        self.zip_file.writestr(filename, csv_content)
    
    def add_metadata(self, metadata: dict):
        """Adiciona arquivo de metadados ao ZIP"""
        import json
        metadata_json = json.dumps(metadata, indent=2, default=str)
        self.zip_file.writestr('_metadata.json', metadata_json)
    
    def finalize(self) -> bytes:
        """Finaliza o ZIP e retorna os bytes"""
        self.zip_file.close()
        zip_bytes = self.zip_buffer.getvalue()
        self.zip_buffer.close()
        return zip_bytes
    
    def get_size_mb(self, zip_bytes: bytes) -> float:
        """Calcula tamanho em MB"""
        return len(zip_bytes) / (1024 * 1024)



class BackupService:
    """
    Serviço principal de backup.
    
    Orquestra o processo de exportação e importação de dados.
    Aplica padrão Facade para simplificar interface complexa.
    """
    
    def __init__(self):
        self.config = BackupConfig()
    
    def exportar_loja(
        self,
        loja_id: int,
        incluir_imagens: bool = False
    ) -> Dict:
        """
        Exporta todos os dados de uma loja em formato CSV compactado.
        
        Args:
            loja_id: ID da loja
            incluir_imagens: Se deve incluir imagens no backup
        
        Returns:
            dict com:
                - success: bool
                - arquivo_nome: str
                - arquivo_bytes: bytes
                - tamanho_mb: float
                - total_registros: int
                - tabelas: dict com contagem por tabela
                - erro: str (se houver erro)
        """
        from .models import Loja
        
        try:
            # Buscar loja (com tipo de app para filtrar tabelas quando schema=public)
            loja = Loja.objects.select_related('tipo_loja').get(id=loja_id)
            
            if not loja.database_created:
                raise BackupExportError("Banco de dados da loja não foi criado")
            
            logger.info(f"🔄 Iniciando exportação de backup - Loja: {loja.nome} (ID: {loja_id})")
            
            # Inicializar helpers
            db_helper = DatabaseHelper(loja.database_name)
            zip_builder = ZipBuilder()
            
            # Estatísticas
            total_registros = 0
            tabelas_stats = {}
            
            # Forçar search_path na conexão (PostgreSQL) para garantir que usamos o schema da loja
            if not db_helper._is_sqlite() and db_helper._pg_schema and is_safe_pg_schema_token(db_helper._pg_schema):
                try:
                    with db_helper.get_connection().cursor() as cursor:
                        cursor.execute(f'SET search_path TO "{db_helper._pg_schema}", public')
                    logger.info(f"Backup: search_path definido para '{db_helper._pg_schema}'")
                except Exception as e:
                    logger.warning(f"Backup: não foi possível SET search_path: {e}")

            # Listar tabelas dinamicamente (qualquer tipo de app: clínica, loja, etc.)
            try:
                table_names = db_helper.get_all_table_names()
            except Exception as e:
                logger.warning(f"⚠️ Fallback para lista fixa de tabelas: {e}")
                table_names = [t.nome for t in self.config.get_tabelas_ordenadas_exportacao()]

            # Quando o backup usa schema PUBLIC (fallback): exportar APENAS tabelas com coluna loja_id
            # e cujo prefixo pertence ao tipo de app da loja (evita cabeleireiro_*, clinica_beleza_*, crm_*, etc.).
            if getattr(db_helper, '_pg_schema', None) == 'public':
                table_names = [t for t in table_names if db_helper._table_has_loja_id(t)]
                tipo_slug = (loja.tipo_loja.slug if loja.tipo_loja else '').strip() or ''
                allowed_prefixes = BACKUP_TIPO_APP_TABLE_PREFIXES.get(tipo_slug, ())
                excluded_prefixes = BACKUP_TIPO_APP_EXCLUDED_PREFIXES.get(tipo_slug, ())
                if allowed_prefixes:
                    def _table_belongs_to_tipo(name: str) -> bool:
                        if any(name.startswith(p) for p in excluded_prefixes):
                            return False
                        return any(name.startswith(p) for p in allowed_prefixes)
                    table_names = [t for t in table_names if _table_belongs_to_tipo(t)]
                if table_names:
                    logger.info(
                        f"Backup (schema public): exportando {len(table_names)} tabela(s) do tipo '{tipo_slug}' (prefixos: {allowed_prefixes})"
                    )

            if not table_names:
                logger.warning(
                    f"⚠️ Nenhuma tabela no schema da loja {loja.nome} (database_name={loja.database_name}, "
                    f"schema_pg={getattr(db_helper, '_pg_schema', 'N/A')}). Verifique se o schema existe e se as migrations foram aplicadas."
                )

            for table_name in table_names:
                if not db_helper.table_exists(table_name):
                    continue
                
                try:
                    # Buscar dados (apenas cadastros da loja: filtro por loja_id quando a tabela tiver essa coluna)
                    columns, records = db_helper.fetch_all_records(
                        table_name, loja_id=loja.id
                    )
                    count = len(records)
                    
                    # Exportar para CSV
                    csv_content = CSVExporter.export_table_to_csv(
                        table_name,
                        columns,
                        records
                    )
                    
                    # Adicionar ao ZIP
                    zip_builder.add_csv(f"{table_name}.csv", csv_content)
                    
                    # Atualizar estatísticas
                    total_registros += count
                    tabelas_stats[table_name] = count
                    
                    logger.info(f"✅ Tabela {table_name}: {count} registros exportados")
                
                except Exception as e:
                    logger.error(f"❌ Erro ao exportar tabela {table_name}: {e}")
                    tabelas_stats[table_name] = 0
            
            # Adicionar metadados (inclui schema efetivo para rastreabilidade quando fallback para public)
            metadata = {
                'loja_id': loja.id,
                'loja_nome': loja.nome,
                'loja_slug': loja.slug,
                'database_name': loja.database_name,
                'schema_exportado': getattr(db_helper, '_pg_schema', loja.database_name or ''),
                'data_backup': timezone.now().isoformat(),
                'total_registros': total_registros,
                'tabelas': tabelas_stats,
                'versao_backup': '1.0',
            }
            zip_builder.add_metadata(metadata)
            
            # Finalizar ZIP
            zip_bytes = zip_builder.finalize()
            tamanho_mb = zip_builder.get_size_mb(zip_bytes)
            
            # Nome do arquivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            arquivo_nome = f"backup_{loja.slug}_{timestamp}.zip"
            
            logger.info(
                f"✅ Backup concluído - {arquivo_nome} - "
                f"{tamanho_mb:.2f} MB - {total_registros} registros"
            )
            
            return {
                'success': True,
                'arquivo_nome': arquivo_nome,
                'arquivo_bytes': zip_bytes,
                'tamanho_mb': tamanho_mb,
                'total_registros': total_registros,
                'tabelas': tabelas_stats,
            }
        
        except Loja.DoesNotExist:
            erro = f"Loja com ID {loja_id} não encontrada"
            logger.error(f"❌ {erro}")
            return {'success': False, 'erro': erro}
        
        except BackupExportError as e:
            erro = str(e)
            logger.error(f"❌ Erro de exportação: {erro}")
            return {'success': False, 'erro': erro}
        
        except Exception as e:
            erro = f"Erro inesperado ao exportar backup: {str(e)}"
            logger.exception(f"❌ {erro}")
            return {'success': False, 'erro': erro}

    
    def importar_loja(
        self,
        loja_id: int,
        arquivo_zip: bytes
    ) -> Dict:
        """
        Importa dados de um arquivo ZIP de backup.
        
        ATENÇÃO: Esta operação é destrutiva e substitui dados existentes.
        
        Args:
            loja_id: ID da loja
            arquivo_zip: Bytes do arquivo ZIP
        
        Returns:
            dict com:
                - success: bool
                - message: str
                - total_registros_importados: int
                - tabelas: dict com contagem por tabela
                - erro: str (se houver erro)
        """
        from .models import Loja
        
        try:
            # Buscar loja (com tipo_loja para filtrar tabelas na importação)
            loja = Loja.objects.select_related('tipo_loja').get(id=loja_id)
            
            if not loja.database_created:
                raise BackupImportError("Banco de dados da loja não foi criado")
            
            logger.info(f"🔄 Iniciando importação de backup - Loja: {loja.nome} (ID: {loja_id})")
            
            # Validar ZIP
            zip_buffer = io.BytesIO(arquivo_zip)
            zip_file = None
            try:
                zip_file = zipfile.ZipFile(zip_buffer, 'r')
            except zipfile.BadZipFile:
                raise BackupImportError("Arquivo ZIP inválido ou corrompido")
            try:
                import json
                try:
                    metadata_content = zip_file.read('_metadata.json')
                    metadata = json.loads(metadata_content)
                    logger.info(f"📋 Metadados do backup: {metadata.get('data_backup')}")
                except KeyError:
                    raise BackupImportError("Arquivo de backup inválido (metadados ausentes)")
                # Restrição: só importar backup na mesma loja de origem (ou loja recriada com mesmo slug)
                backup_loja_id = metadata.get('loja_id')
                backup_loja_slug = metadata.get('loja_slug', '').strip()
                if backup_loja_id is None:
                    raise BackupImportError("Arquivo de backup inválido (loja de origem não identificada)")
                # Permitir: mesmo loja_id OU mesmo slug (loja recriada após exclusão)
                mesmo_id = int(backup_loja_id) == int(loja_id)
                mesmo_slug = backup_loja_slug and backup_loja_slug == (loja.slug or '')
                if not mesmo_id and not mesmo_slug:
                    raise BackupImportError(
                        f"Este backup pertence à loja '{metadata.get('loja_nome', 'outra')}'. "
                        "Só é possível importar backups exportados desta loja."
                    )
                # Configurar conexão da loja
                from core.db_config import ensure_loja_database_config
                if not ensure_loja_database_config(loja.database_name, conn_max_age=60):
                    raise BackupImportError("Não foi possível conectar ao banco de dados da loja")
                
                db_helper = DatabaseHelper(loja.database_name)
                # Se schema vazio (loja recém-criada, migrate pode ter criado em public): aplicar migrations + fallback
                if not db_helper._is_sqlite() and db_helper._pg_schema:
                    with db_helper.get_connection().cursor() as cur:
                        cur.execute(
                            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s AND table_type = 'BASE TABLE' AND table_name NOT LIKE 'django_%%'",
                            [db_helper._pg_schema],
                        )
                        if cur.fetchone()[0] == 0:
                            logger.info(f"Schema '{db_helper._pg_schema}' vazio - aplicando migrations antes da importação")
                            from django.db import connections
                            DatabaseSchemaService.aplicar_migrations(loja)
                            try:
                                connections[loja.database_name].close()
                            except Exception:
                                pass
                            # Re-verificar
                            with db_helper.get_connection().cursor() as cur2:
                                cur2.execute(
                                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s AND table_type = 'BASE TABLE' AND table_name NOT LIKE 'django_%%'",
                                    [db_helper._pg_schema],
                                )
                                if cur2.fetchone()[0] == 0:
                                    raise BackupImportError(
                                        "A loja não possui tabelas configuradas. "
                                        "Entre em contato com o suporte para configurar o banco."
                                    )
                
                # Estatísticas
                total_registros = 0
                tabelas_stats = {}
                
                # Montar lista de (table_name, csv_filename): lista fixa + CSVs do ZIP (backup dinâmico)
                tabelas = self.config.get_tabelas_ordenadas_importacao()
                processar = []
                vistos = set()
                for t in tabelas:
                    fn = f"{t.nome}.csv"
                    if fn in zip_file.namelist() and t.nome not in vistos:
                        processar.append((t.nome, fn))
                        vistos.add(t.nome)
                for nome in zip_file.namelist():
                    if nome.endswith(".csv") and nome != "_metadata.json":
                        table_name = nome[:-4]
                        if table_name not in vistos:
                            processar.append((table_name, nome))
                            vistos.add(table_name)
                
                # ✅ OTIMIZAÇÃO: Filtrar tabelas por tipo da loja (mesmo critério da exportação).
                # Evita ~50 queries desnecessárias de table_exists para módulos inativos.
                tipo_slug = (loja.tipo_loja.slug if loja.tipo_loja else '').strip() if hasattr(loja, 'tipo_loja') else ''
                allowed_prefixes = BACKUP_TIPO_APP_TABLE_PREFIXES.get(tipo_slug, ())
                excluded_prefixes = BACKUP_TIPO_APP_EXCLUDED_PREFIXES.get(tipo_slug, ())
                if allowed_prefixes:
                    def _table_allowed_for_import(name):
                        if any(name.startswith(p) for p in excluded_prefixes):
                            return False
                        return any(name.startswith(p) for p in allowed_prefixes)
                    antes = len(processar)
                    processar = [(t, f) for t, f in processar if _table_allowed_for_import(t)]
                    if antes != len(processar):
                        logger.info(
                            f"Importação: filtrado {antes - len(processar)} tabela(s) não pertencentes ao tipo '{tipo_slug}'"
                        )
                
                with transaction.atomic(using=loja.database_name):
                    if (
                        not db_helper._is_sqlite()
                        and is_safe_pg_schema_token(db_helper._pg_schema)
                    ):
                        with db_helper.get_connection().cursor() as _spc:
                            sch = db_helper._pg_schema.replace('"', "")
                            _spc.execute(
                                f'SET LOCAL search_path TO "{sch}", public'
                            )
                    for table_name, csv_filename in processar:
                        # Verificar se tabela existe e nome é seguro
                        if not DatabaseHelper.is_safe_table_name(table_name):
                            continue
                        if not db_helper.table_exists(table_name):
                            logger.warning(f"⚠️ Tabela {table_name} não existe no banco da loja")
                            continue
                        
                        try:
                            # Ler CSV
                            csv_content = zip_file.read(csv_filename).decode('utf-8')
                            csv_reader = csv.DictReader(io.StringIO(csv_content))
                            rows = list(csv_reader)
                            if not rows:
                                tabelas_stats[table_name] = 0
                                continue

                            if table_name == "crm_vendas_config":
                                qual = db_helper.qualified_table_name(table_name)
                                _import_crm_vendas_config_via_model(
                                    loja,
                                    rows,
                                    qual,
                                    loja.database_name,
                                    db_helper._pg_schema,
                                )
                                ncfg = len(rows)
                                total_registros += ncfg
                                tabelas_stats[table_name] = ncfg
                                logger.info(
                                    "✅ Tabela %s: %s registros importados (INSERT explícito CRMConfig)",
                                    table_name,
                                    ncfg,
                                )
                                continue
                            
                            # Colunas da tabela no banco (ordem e nomes)
                            db_columns = db_helper.get_table_columns(table_name)
                            col_info = db_helper.get_columns_nullable_and_type(table_name)
                            if table_name == "crm_vendas_config" and not db_helper._is_sqlite():
                                pg_cols, pg_info = db_helper.get_pg_table_meta_for_backup(
                                    table_name
                                )
                                if pg_cols:
                                    db_columns = pg_cols
                                if pg_info:
                                    col_info = pg_info
                            if not db_columns:
                                logger.warning(
                                    f"⚠️ Não foi possível obter colunas da tabela {table_name}"
                                )
                                continue
                            
                            # Usar apenas colunas que existem no CSV e na tabela (ordem da tabela)
                            # Filtrar também por nome seguro (defesa em profundidade)
                            csv_headers = list(rows[0].keys()) if rows else []
                            csv_header_set = set(csv_headers)
                            cols_for_insert = []
                            for c in db_columns:
                                if not DatabaseHelper.is_safe_table_name(c):
                                    continue
                                if c in csv_header_set:
                                    cols_for_insert.append(c)
                                elif (
                                    table_name == "crm_vendas_config"
                                    and c in BACKUP_CRM_CONFIG_EXTRA_INT_COLUMNS
                                ):
                                    cols_for_insert.append(c)
                            if table_name == "crm_vendas_config":
                                missing_issnet = [
                                    c
                                    for c in BACKUP_CRM_CONFIG_EXTRA_INT_COLUMNS
                                    if c in db_columns and c not in cols_for_insert
                                ]
                                if missing_issnet:
                                    merged = set(cols_for_insert) | set(missing_issnet)
                                    cols_for_insert = [
                                        c
                                        for c in db_columns
                                        if c in merged
                                        and DatabaseHelper.is_safe_table_name(c)
                                    ]
                            if not cols_for_insert:
                                logger.warning(f"⚠️ Nenhuma coluna comum entre CSV e tabela {table_name}")
                                tabelas_stats[table_name] = 0
                                continue
                            
                            # Limpar tabela antes de importar (qualificado para PostgreSQL)
                            qual = db_helper.qualified_table_name(table_name)
                            with db_helper.get_connection().cursor() as cursor:
                                cursor.execute(f"DELETE FROM {qual}")
                                
                                # INSERT com placeholders (%s funciona em Django para SQLite e PostgreSQL)
                                placeholders = ", ".join(["%s"] * len(cols_for_insert))
                                cols_str = ", ".join(cols_for_insert)
                                insert_sql = f"INSERT INTO {qual} ({cols_str}) VALUES ({placeholders})"
                                
                                for row in rows:
                                    values = []
                                    for col in cols_for_insert:
                                        # Usar loja_id da loja atual (mesma loja de origem)
                                        if col == 'loja_id':
                                            val = loja.id
                                        else:
                                            raw = row.get(col)
                                            val = "" if raw is None else raw
                                        if isinstance(val, str):
                                            stripped = val.strip()
                                            if stripped == "" or stripped.lower() in (
                                                "null",
                                                "none",
                                                "nan",
                                            ):
                                                val = None
                                        elif val == "" and col != "id":
                                            val = None
                                        # Colunas NOT NULL: CSV vazio vira None; BD exige valor (texto, int, bool, etc.)
                                        if val is None and col != "id":
                                            nullable, dtype = col_info.get(col, (True, ''))
                                            dt = (dtype or "").lower().split("(")[0].strip()
                                            if not nullable:
                                                if dt in (
                                                    "text",
                                                    "character varying",
                                                    "varchar",
                                                    "char",
                                                    "character",
                                                ) or "varchar" in (dtype or "").lower():
                                                    val = ""
                                                elif dt in (
                                                    "integer",
                                                    "bigint",
                                                    "smallint",
                                                    "serial",
                                                    "bigserial",
                                                    "smallserial",
                                                ):
                                                    val = 0
                                                elif dt == "boolean":
                                                    val = False
                                                elif dt in ("numeric", "decimal"):
                                                    val = Decimal("0")
                                                elif dt in ("real", "double precision"):
                                                    val = 0.0
                                        # col_info pode falhar (schema); int obrigatórios do CRM
                                        if (
                                            val is None
                                            and col != "id"
                                            and table_name == "crm_vendas_config"
                                            and col in BACKUP_CRM_CONFIG_EXTRA_INT_COLUMNS
                                        ):
                                            val = 0
                                        values.append(val)
                                    if table_name == "crm_vendas_config":
                                        values = _backup_finalize_crm_config_row_values(
                                            cols_for_insert, values
                                        )
                                    cursor.execute(insert_sql, values)
                            
                            count = len(rows)
                            total_registros += count
                            tabelas_stats[table_name] = count
                            
                            logger.info(f"✅ Tabela {table_name}: {count} registros importados")
                        
                        except Exception as e:
                            logger.error(f"❌ Erro ao importar tabela {table_name}: {e}")
                            raise BackupImportError(f"Erro ao importar {table_name}: {str(e)}")
                
                # PostgreSQL: resetar sequences após INSERT com IDs explícitos (evita conflito em novos registros)
                if not db_helper._is_sqlite() and db_helper._pg_schema and is_safe_pg_schema_token(db_helper._pg_schema):
                    with db_helper.get_connection().cursor() as cursor:
                        for table_name, _ in processar:
                            if not DatabaseHelper.is_safe_table_name(table_name) or not db_helper.table_exists(table_name):
                                continue
                            cols = db_helper.get_table_columns(table_name)
                            if 'id' not in cols:
                                continue
                            qual = db_helper.qualified_table_name(table_name)
                            try:
                                seq_rel = (
                                    f'"{db_helper._pg_schema}"."{table_name}"'
                                    if is_safe_pg_schema_token(db_helper._pg_schema)
                                    else qual
                                )
                                cursor.execute(
                                    f"SELECT setval(pg_get_serial_sequence(%s, 'id'), "
                                    f"(SELECT COALESCE(MAX(id), 1) FROM {qual}))",
                                    [seq_rel],
                                )
                            except Exception as e:
                                logger.warning(f"⚠️ Não foi possível resetar sequence de {table_name}: {e}")
                
                logger.info(f"✅ Importação concluída - {total_registros} registros importados")
                
                # Invalidar cache do CRM para que o frontend exiba dados atualizados
                try:
                    from crm_vendas.cache import CRMCacheManager
                    CRMCacheManager.invalidate_dashboard(loja.id)
                    CRMCacheManager.invalidate_leads(loja.id)
                    CRMCacheManager.invalidate_contas(loja.id)
                    CRMCacheManager.invalidate_contatos(loja.id)
                    CRMCacheManager.invalidate_oportunidades(loja.id)
                    CRMCacheManager.invalidate_atividades(loja.id)
                    logger.info(f"Cache CRM invalidado para loja {loja.nome}")
                except Exception as e:
                    logger.warning(f"Cache invalidation: {e}")
                
                return {
                    'success': True,
                    'message': f'Backup importado com sucesso. {total_registros} registros restaurados.',
                    'total_registros_importados': total_registros,
                    'tabelas': tabelas_stats,
                }
            finally:
                try:
                    if zip_file is not None:
                        zip_file.close()
                finally:
                    zip_buffer.close()
        
        except Loja.DoesNotExist:
            erro = f"Loja com ID {loja_id} não encontrada"
            logger.error(f"❌ {erro}")
            return {'success': False, 'erro': erro}
        
        except BackupImportError as e:
            erro = str(e)
            logger.error(f"❌ Erro de importação: {erro}")
            return {'success': False, 'erro': erro}
        
        except Exception as e:
            erro = f"Erro inesperado ao importar backup: {str(e)}"
            logger.exception(f"❌ {erro}")
            return {'success': False, 'erro': erro}
