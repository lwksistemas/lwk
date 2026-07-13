"""Orquestração de exportação e importação de backup de lojas."""
import contextlib
import csv
import io
import logging
import zipfile
from datetime import datetime
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from ..backup_helpers import (
    BACKUP_CRM_CONFIG_EXTRA_INT_COLUMNS,
    BACKUP_TIPO_APP_EXCLUDED_PREFIXES,
    BACKUP_TIPO_APP_TABLE_PREFIXES,
    BackupExportError,
    BackupImportError,
    _backup_finalize_crm_config_row_values,
    _connection_is_postgresql,
    _ensure_crm_vendas_config_pg_int_defaults,
    _import_crm_vendas_config_via_model,
    _is_crm_issnet_int_col,
    _normalize_backup_csv_row_keys,
    _sanitize_pg_table_key,
    _truncate_backup_value_for_pg_type,
    _zip_csv_basename_table_name,
    is_safe_pg_schema_token,
)
from .config import BackupConfig
from .database_helper import DatabaseHelper
from .exporters import CSVExporter, ZipBuilder

logger = logging.getLogger(__name__)

def _filtrar_tabelas_schema_public(db_helper, loja, table_names: list) -> list:
    """Quando schema é public, filtra tabelas por loja_id e prefixo do tipo de app."""
    table_names = [t for t in table_names if db_helper._table_has_loja_id(t)]
    tipo_slug = (loja.tipo_loja.slug if loja.tipo_loja else "").strip() or ""
    allowed_prefixes = BACKUP_TIPO_APP_TABLE_PREFIXES.get(tipo_slug, ())
    excluded_prefixes = BACKUP_TIPO_APP_EXCLUDED_PREFIXES.get(tipo_slug, ())
    if allowed_prefixes:
        def _pertence(name: str) -> bool:
            if any(name.startswith(p) for p in excluded_prefixes):
                return False
            return any(name.startswith(p) for p in allowed_prefixes)
        table_names = [t for t in table_names if _pertence(t)]
    if table_names:
        logger.info(
            "Backup (schema public): exportando %d tabela(s) do tipo '%s' (prefixos: %s)",
            len(table_names), tipo_slug, allowed_prefixes,
        )
    return table_names


def _preparar_tabelas_backup(db_helper, config, loja) -> list:
    """Define search_path PostgreSQL e retorna lista de tabelas a exportar."""
    if not db_helper._is_sqlite() and db_helper._pg_schema and is_safe_pg_schema_token(db_helper._pg_schema):
        try:
            with db_helper.get_connection().cursor() as cursor:
                cursor.execute(f'SET search_path TO "{db_helper._pg_schema}", public')
            logger.info("Backup: search_path definido para '%s'", db_helper._pg_schema)
        except Exception as e:
            logger.warning("Backup: não foi possível SET search_path: %s", e)
    try:
        table_names = db_helper.get_all_table_names()
    except Exception as e:
        logger.warning("⚠️ Fallback para lista fixa de tabelas: %s", e)
        table_names = [t.nome for t in config.get_tabelas_ordenadas_exportacao()]
    if getattr(db_helper, "_pg_schema", None) == "public":
        table_names = _filtrar_tabelas_schema_public(db_helper, loja, table_names)
    if not table_names:
        logger.warning(
            "⚠️ Nenhuma tabela no schema da loja %s (database_name=%s, schema_pg=%s). "
            "Verifique se o schema existe e se as migrations foram aplicadas.",
            loja.nome, loja.database_name, getattr(db_helper, "_pg_schema", "N/A"),
        )
    return table_names


def _finalizar_zip_backup(loja, db_helper, zip_builder, table_names, total_registros, tabelas_stats, incluir_imagens, imagens_stats) -> dict:
    """Adiciona metadados, finaliza o ZIP e retorna dict de sucesso."""
    metadata = {
        "loja_id": loja.id,
        "loja_nome": loja.nome,
        "loja_slug": loja.slug,
        "database_name": loja.database_name,
        "schema_exportado": getattr(db_helper, "_pg_schema", loja.database_name or ""),
        "data_backup": timezone.now().isoformat(),
        "total_registros": total_registros,
        "tabelas": tabelas_stats,
        "incluir_imagens": incluir_imagens,
        "imagens": imagens_stats,
        "versao_backup": "1.1",
    }
    zip_builder.add_metadata(metadata)
    zip_bytes = zip_builder.finalize()
    tamanho_mb = zip_builder.get_size_mb(zip_bytes)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    arquivo_nome = f"backup_{loja.slug}_{timestamp}.zip"
    logger.info("✅ Backup concluído - %s - %.2f MB - %d registros", arquivo_nome, tamanho_mb, total_registros)
    return {"success": True, "arquivo_nome": arquivo_nome, "arquivo_bytes": zip_bytes,
            "tamanho_mb": tamanho_mb, "total_registros": total_registros, "tabelas": tabelas_stats, "imagens": imagens_stats}


def _exportar_tabelas_para_zip(db_helper, zip_builder, table_names: list, loja_id: int) -> tuple[int, dict]:
    """Itera tabelas, exporta CSV e adiciona ao ZIP. Retorna (total_registros, tabelas_stats)."""
    total_registros = 0
    tabelas_stats = {}
    for table_name in table_names:
        if not db_helper.table_exists(table_name):
            continue
        try:
            columns, records = db_helper.fetch_all_records(table_name, loja_id=loja_id)
            count = len(records)
            csv_content = CSVExporter.export_table_to_csv(table_name, columns, records)
            zip_builder.add_csv(f"{table_name}.csv", csv_content)
            total_registros += count
            tabelas_stats[table_name] = count
            logger.info("✅ Tabela %s: %d registros exportados", table_name, count)
        except Exception as e:
            logger.error("❌ Erro ao exportar tabela %s: %s", table_name, e)
            tabelas_stats[table_name] = 0
    return total_registros, tabelas_stats


class BackupService:
    """Serviço principal de backup.

    Orquestra o processo de exportação e importação de dados.
    Aplica padrão Facade para simplificar interface complexa.
    """

    def __init__(self):
        self.config = BackupConfig()

    def exportar_loja(
        self,
        loja_id: int,
        incluir_imagens: bool = False,
    ) -> dict:
        """Exporta todos os dados de uma loja em formato CSV compactado.

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
        from superadmin.models import Loja

        try:
            # Buscar loja (com tipo de app para filtrar tabelas quando schema=public)
            loja = Loja.objects.select_related("tipo_loja").get(id=loja_id)

            if not loja.database_created:
                raise BackupExportError("Banco de dados da loja não foi criado")

            logger.info(f"🔄 Iniciando exportação de backup - Loja: {loja.nome} (ID: {loja_id})")

            # Inicializar helpers
            db_helper = DatabaseHelper(loja.database_name)
            zip_builder = ZipBuilder()
            table_names = _preparar_tabelas_backup(db_helper, self.config, loja)
            total_registros, tabelas_stats = _exportar_tabelas_para_zip(db_helper, zip_builder, table_names, loja.id)
            imagens_stats = None
            if incluir_imagens:
                from .image_exporter import BackupImageExporter
                logger.info("🖼️ Incluindo imagens no backup da loja %s", loja.nome)
                image_exporter = BackupImageExporter(loja, db_helper)
                imagens_stats = image_exporter.export_to_zip(zip_builder, table_names, loja.id)
                logger.info("🖼️ Imagens no backup: %d arquivo(s), %.2f MB",
                    imagens_stats.get("total_arquivos", 0), imagens_stats.get("total_bytes", 0) / (1024 * 1024))
            return _finalizar_zip_backup(loja, db_helper, zip_builder, table_names, total_registros, tabelas_stats, incluir_imagens, imagens_stats)

        except Loja.DoesNotExist:
            erro = f"Loja com ID {loja_id} não encontrada"
            logger.error(f"❌ {erro}")
            return {"success": False, "erro": erro}

        except BackupExportError as e:
            erro = str(e)
            logger.error(f"❌ Erro de exportação: {erro}")
            return {"success": False, "erro": erro}

        except Exception as e:
            erro = f"Erro inesperado ao exportar backup: {e!s}"
            logger.exception(f"❌ {erro}")
            return {"success": False, "erro": erro}


    # ------------------------------------------------------------------
    # Helpers internos do importar_loja
    # ------------------------------------------------------------------

    def _validate_zip_metadata(self, zip_file, loja_id, loja):
        """Lê e valida _metadata.json do ZIP. Levanta BackupImportError se inválido."""
        import json
        try:
            metadata = json.loads(zip_file.read("_metadata.json"))
        except KeyError:
            raise BackupImportError("Arquivo de backup inválido (metadados ausentes)")
        logger.info(f"📋 Metadados do backup: {metadata.get('data_backup')}")
        backup_loja_id = metadata.get("loja_id")
        if backup_loja_id is None:
            raise BackupImportError("Arquivo de backup inválido (loja de origem não identificada)")
        mesmo_id = int(backup_loja_id) == int(loja_id)
        mesmo_slug = (metadata.get("loja_slug") or "").strip() == (loja.slug or "")
        if not mesmo_id and not mesmo_slug:
            raise BackupImportError(
                f"Este backup pertence à loja '{metadata.get('loja_nome', 'outra')}'. "
                "Só é possível importar backups exportados desta loja.",
            )

    def _ensure_schema_tables(self, loja, db_helper):
        """Garante que o schema da loja tem tabelas; aplica migrations se vazio."""
        if db_helper._is_sqlite() or not db_helper._pg_schema:
            return
        sql = (
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema = %s AND table_type = 'BASE TABLE' AND table_name NOT LIKE 'django_%%'"
        )
        with db_helper.get_connection().cursor() as cur:
            cur.execute(sql, [db_helper._pg_schema])
            if cur.fetchone()[0] > 0:
                return
        logger.info(f"Schema '{db_helper._pg_schema}' vazio - aplicando migrations antes da importação")
        from django.db import connections

        from superadmin.services.database_schema_service import DatabaseSchemaService
        DatabaseSchemaService.aplicar_migrations(loja)
        with contextlib.suppress(Exception):
            connections[loja.database_name].close()
        with db_helper.get_connection().cursor() as cur2:
            cur2.execute(sql, [db_helper._pg_schema])
            if cur2.fetchone()[0] == 0:
                raise BackupImportError("A loja não possui tabelas configuradas. Entre em contato com o suporte.")

    def _build_processar_list(self, zip_file):
        """Monta lista de (table_name, csv_filename) a partir das tabelas config + CSVs dinâmicos do ZIP."""
        tabelas = self.config.get_tabelas_ordenadas_importacao()
        processar = []
        vistos = set()
        zip_names = zip_file.namelist()
        for t in tabelas:
            fn = f"{t.nome}.csv"
            match_fn = fn if fn in zip_names else next(
                (zn for zn in zip_names if zn.replace("\\", "/").endswith("/" + fn) or zn == fn), None
            )
            if match_fn is not None and t.nome not in vistos:
                processar.append((t.nome, match_fn))
                vistos.add(t.nome)
        for nome in zip_names:
            if nome.endswith(".csv") and nome != "_metadata.json":
                table_name = _zip_csv_basename_table_name(nome)
                if table_name not in vistos:
                    processar.append((table_name, nome))
                    vistos.add(table_name)
        return processar

    def _filter_processar_by_tipo(self, processar, loja):
        """Filtra lista de processar pelo tipo de app da loja (evita queries desnecessárias)."""
        tipo_slug = (loja.tipo_loja.slug if loja.tipo_loja else "").strip() if hasattr(loja, "tipo_loja") else ""
        allowed = BACKUP_TIPO_APP_TABLE_PREFIXES.get(tipo_slug, ())
        excluded = BACKUP_TIPO_APP_EXCLUDED_PREFIXES.get(tipo_slug, ())
        if not allowed:
            return processar
        def _allowed(name):
            return not any(name.startswith(p) for p in excluded) and any(name.startswith(p) for p in allowed)
        antes = len(processar)
        result = [(t, f) for t, f in processar if _allowed(t)]
        if antes != len(result):
            logger.info(f"Importação: filtrado {antes - len(result)} tabela(s) não pertencentes ao tipo '{tipo_slug}'")
        return result

    @staticmethod
    def _resolver_cols_para_insert(table_name: str, db_columns: list, csv_header_set: set) -> list:
        """Retorna lista de colunas válidas para INSERT, resolvendo extras do crm_vendas_config."""
        cols = [
            c for c in db_columns
            if DatabaseHelper.is_safe_table_name(c) and (
                c in csv_header_set or (table_name == "crm_vendas_config" and _is_crm_issnet_int_col(c))
            )
        ]
        if table_name == "crm_vendas_config":
            missing = [
                next((d for d in db_columns if (d or "").strip().lower() == lg), None)
                for lg in BACKUP_CRM_CONFIG_EXTRA_INT_COLUMNS
            ]
            for actual in missing:
                if actual and actual not in cols:
                    cols = [c for c in db_columns if c in set(cols) | {actual} and DatabaseHelper.is_safe_table_name(c)]
        return cols

    @staticmethod
    def _normalizar_str_csv(val, col: str):
        """Converte string vazia/null/nan para None; retorna val inalterado caso contrário."""
        if isinstance(val, str):
            stripped = val.strip()
            if stripped == "" or stripped.lower() in ("null", "none", "nan"):
                return None
        elif val == "" and col != "id":
            return None
        return val

    @staticmethod
    def _coerce_null_by_dtype(dt: str, dtype: str):
        """Retorna valor padrão não-nulo para um dtype PostgreSQL quando nullable=False."""
        if dt in ("text", "character varying", "varchar", "char", "character") or "varchar" in (dtype or "").lower():
            return ""
        if dt in ("integer", "bigint", "smallint", "serial", "bigserial", "smallserial"):
            return 0
        if dt == "boolean":
            return False
        if dt in ("numeric", "decimal"):
            return Decimal(0)
        if dt in ("real", "double precision"):
            return 0.0
        return None

    @staticmethod
    def _coerce_csv_value(val, col, col_info, table_name):
        """Normaliza um valor de célula CSV para o tipo correto do banco."""
        val = BackupService._normalizar_str_csv(val, col)
        if val is None and col != "id":
            nullable, dtype = col_info.get(col, col_info.get((col or "").strip(), (True, "")))
            dt = (dtype or "").lower().split("(")[0].strip()
            if not nullable:
                coerced = BackupService._coerce_null_by_dtype(dt, dtype)
                if coerced is not None:
                    val = coerced
        if val is None and col != "id" and table_name == "crm_vendas_config" and _is_crm_issnet_int_col(col):
            val = 0
        _, dtype = col_info.get(col, col_info.get((col or "").strip(), (True, "")))
        return _truncate_backup_value_for_pg_type(val, dtype)

    def _import_table_rows(self, cursor, loja, db_helper, table_name, rows, col_info, db_columns):
        """Limpa a tabela e insere todas as linhas do CSV."""
        qual = db_helper.qualified_table_name(table_name)
        if table_name == "crm_vendas_config" and not db_helper._is_sqlite() and _connection_is_postgresql(db_helper.get_connection()):
            _ensure_crm_vendas_config_pg_int_defaults(cursor, qual)
        cursor.execute(f"DELETE FROM {qual}")
        csv_header_set = set(rows[0].keys())
        cols_for_insert = BackupService._resolver_cols_para_insert(table_name, db_columns, csv_header_set)
        if not cols_for_insert:
            logger.warning(f"⚠️ Nenhuma coluna comum entre CSV e tabela {table_name}")
            return 0
        insert_sql = f"INSERT INTO {qual} ({', '.join(cols_for_insert)}) VALUES ({', '.join(['%s'] * len(cols_for_insert))})"
        for row in rows:
            values = [
                self._coerce_csv_value(loja.id if col == "loja_id" else (row.get(col) or ""), col, col_info, table_name)
                for col in cols_for_insert
            ]
            if table_name == "crm_vendas_config":
                values = _backup_finalize_crm_config_row_values(cols_for_insert, values)
            cursor.execute(insert_sql, values)
        return len(rows)

    def _import_processar_uma_tabela(self, zip_file, table_name: str, csv_filename: str, loja, db_helper) -> int | None:
        """Importa uma única tabela do zip. Retorna contagem de registros ou None para skip."""
        table_name = _sanitize_pg_table_key(table_name)
        if _zip_csv_basename_table_name(csv_filename).lower() == "crm_vendas_config":
            table_name = "crm_vendas_config"
        if not DatabaseHelper.is_safe_table_name(table_name) or not db_helper.table_exists(table_name):
            if DatabaseHelper.is_safe_table_name(table_name):
                logger.warning(f"⚠️ Tabela {table_name} não existe no banco da loja")
            return None
        rows = [_normalize_backup_csv_row_keys(r) for r in csv.DictReader(io.StringIO(zip_file.read(csv_filename).decode("utf-8")))]
        if not rows:
            return 0
        if table_name == "crm_vendas_config":
            qual = db_helper.qualified_table_name(table_name)
            _import_crm_vendas_config_via_model(loja, rows, qual, loja.database_name, db_helper._pg_schema)
            logger.info("✅ Tabela %s: %s registros importados (INSERT explícito CRMConfig)", table_name, len(rows))
            return len(rows)
        db_columns = [str(c).strip() for c in db_helper.get_table_columns(table_name) if c is not None and str(c).strip()]
        col_info = db_helper.get_columns_nullable_and_type(table_name)
        if not db_helper._is_sqlite():
            pg_cols, pg_info = db_helper.get_pg_table_meta_for_backup(table_name)
            if pg_cols:
                db_columns = pg_cols
            if pg_info:
                col_info = pg_info
        if not db_columns:
            logger.warning(f"⚠️ Não foi possível obter colunas da tabela {table_name}")
            return None
        with db_helper.get_connection().cursor() as cursor:
            return self._import_table_rows(cursor, loja, db_helper, table_name, rows, col_info, db_columns)

    def _import_processar_tables(self, zip_file, loja, db_helper, processar):
        """Importa todas as tabelas da lista processar dentro de uma transação atômica."""
        total_registros = 0
        tabelas_stats = {}
        with transaction.atomic(using=loja.database_name):
            if not db_helper._is_sqlite() and is_safe_pg_schema_token(db_helper._pg_schema):
                with db_helper.get_connection().cursor() as _spc:
                    sch = db_helper._pg_schema.replace('"', "")
                    _spc.execute(f'SET LOCAL search_path TO "{sch}", public')
            for table_name, csv_filename in processar:
                try:
                    count = self._import_processar_uma_tabela(zip_file, table_name, csv_filename, loja, db_helper)
                    if count is None:
                        continue
                    tabelas_stats[_sanitize_pg_table_key(table_name)] = count
                    if count:
                        total_registros += count
                        logger.info(f"✅ Tabela {table_name}: {count} registros importados")
                except Exception as e:
                    logger.error(f"❌ Erro ao importar tabela {table_name}: {e}")
                    raise BackupImportError(f"Erro ao importar {table_name}: {e!s}")
        return total_registros, tabelas_stats

    def _reset_pg_sequences(self, db_helper, processar):
        """Reseta sequences PostgreSQL após INSERT com IDs explícitos."""
        if db_helper._is_sqlite() or not db_helper._pg_schema or not is_safe_pg_schema_token(db_helper._pg_schema):
            return
        with db_helper.get_connection().cursor() as cursor:
            for table_name, _ in processar:
                if not DatabaseHelper.is_safe_table_name(table_name) or not db_helper.table_exists(table_name):
                    continue
                if "id" not in db_helper.get_table_columns(table_name):
                    continue
                qual = db_helper.qualified_table_name(table_name)
                seq_rel = f'"{db_helper._pg_schema}"."{table_name}"' if is_safe_pg_schema_token(db_helper._pg_schema) else qual
                try:
                    cursor.execute(
                        f"SELECT setval(pg_get_serial_sequence(%s, 'id'), (SELECT COALESCE(MAX(id), 1) FROM {qual}))",
                        [seq_rel],
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Não foi possível resetar sequence de {table_name}: {e}")

    def _invalidate_crm_cache(self, loja):
        """Invalida cache CRM após importação."""
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

    def importar_loja(
        self,
        loja_id: int,
        arquivo_zip: bytes,
    ) -> dict:
        """Importa dados de um arquivo ZIP de backup.

        ATENÇÃO: Esta operação é destrutiva e substitui dados existentes.
        """
        from superadmin.models import Loja

        try:
            loja = Loja.objects.select_related("tipo_loja").get(id=loja_id)
            if not loja.database_created:
                raise BackupImportError("Banco de dados da loja não foi criado")
            logger.info(f"🔄 Iniciando importação de backup - Loja: {loja.nome} (ID: {loja_id})")

            zip_buffer = io.BytesIO(arquivo_zip)
            zip_file = None
            try:
                zip_file = zipfile.ZipFile(zip_buffer, "r")
            except zipfile.BadZipFile:
                raise BackupImportError("Arquivo ZIP inválido ou corrompido")
            try:
                self._validate_zip_metadata(zip_file, loja_id, loja)

                from core.db_config import ensure_loja_database_config
                if not ensure_loja_database_config(loja.database_name, conn_max_age=60):
                    raise BackupImportError("Não foi possível conectar ao banco de dados da loja")

                db_helper = DatabaseHelper(loja.database_name)
                self._ensure_schema_tables(loja, db_helper)

                processar = self._build_processar_list(zip_file)
                processar = self._filter_processar_by_tipo(processar, loja)

                total_registros, tabelas_stats = self._import_processar_tables(zip_file, loja, db_helper, processar)
                self._reset_pg_sequences(db_helper, processar)

                logger.info(f"✅ Importação concluída - {total_registros} registros importados")
                self._invalidate_crm_cache(loja)

                return {
                    "success": True,
                    "message": f"Backup importado com sucesso. {total_registros} registros restaurados.",
                    "total_registros_importados": total_registros,
                    "tabelas": tabelas_stats,
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
            return {"success": False, "erro": erro}
        except BackupImportError as e:
            erro = str(e)
            logger.error(f"❌ Erro de importação: {erro}")
            return {"success": False, "erro": erro}
        except Exception as e:
            erro = f"Erro inesperado ao importar backup: {e!s}"
            logger.exception(f"❌ {erro}")
            return {"success": False, "erro": erro}
