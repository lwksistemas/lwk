"""Orquestração de exportação e importação de backup de lojas."""
import csv
import io
import json
import logging
import os
import re
import zipfile
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings
from django.core.mail import EmailMessage
from django.db import connections, transaction
from django.utils import timezone

from ..backup_helpers import (
    BACKUP_CRM_CONFIG_EXTRA_INT_COLUMNS,
    BACKUP_SAFE_IDENTIFIER_RE,
    BACKUP_SAFE_PG_SCHEMA_RE,
    BACKUP_TIPO_APP_EXCLUDED_PREFIXES,
    BACKUP_TIPO_APP_TABLE_PREFIXES,
    BackupExportError,
    BackupImportError,
    _backup_finalize_crm_config_row_values,
    _coerce_int_or_zero,
    _connection_is_postgresql,
    _ensure_crm_vendas_config_pg_int_defaults,
    _fetch_crm_vendas_config_pg_colrows,
    _import_crm_vendas_config_via_model,
    _is_crm_issnet_int_col,
    _normalize_backup_csv_row_keys,
    _parse_pg_qualified_table,
    _resolve_visible_pg_schema_for_table,
    _sanitize_pg_table_key,
    _zip_csv_basename_table_name,
    is_safe_pg_schema_token,
)
from .config import BackupConfig
from .database_helper import DatabaseHelper
from .exporters import CSVExporter, ZipBuilder

logger = logging.getLogger(__name__)

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
        from superadmin.models import Loja
        
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

            imagens_stats = None
            if incluir_imagens:
                from .image_exporter import BackupImageExporter

                logger.info(f"🖼️ Incluindo imagens no backup da loja {loja.nome}")
                image_exporter = BackupImageExporter(loja, db_helper)
                imagens_stats = image_exporter.export_to_zip(zip_builder, table_names, loja.id)
                logger.info(
                    f"🖼️ Imagens no backup: {imagens_stats.get('total_arquivos', 0)} arquivo(s), "
                    f"{imagens_stats.get('total_bytes', 0) / (1024 * 1024):.2f} MB"
                )
            
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
                'incluir_imagens': incluir_imagens,
                'imagens': imagens_stats,
                'versao_backup': '1.1',
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
                'imagens': imagens_stats,
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
        from superadmin.models import Loja
        
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
                            from superadmin.services.database_schema_service import DatabaseSchemaService
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
                    match_fn = None
                    if fn in zip_file.namelist():
                        match_fn = fn
                    else:
                        for zn in zip_file.namelist():
                            znorm = zn.replace("\\", "/")
                            if znorm.endswith("/" + fn) or znorm == fn:
                                match_fn = zn
                                break
                    if match_fn is not None and t.nome not in vistos:
                        processar.append((t.nome, match_fn))
                        vistos.add(t.nome)
                for nome in zip_file.namelist():
                    if nome.endswith(".csv") and nome != "_metadata.json":
                        table_name = _zip_csv_basename_table_name(nome)
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
                        table_name = _sanitize_pg_table_key(table_name)
                        csv_base = _zip_csv_basename_table_name(csv_filename)
                        if (
                            table_name.lower() == "crm_vendas_config"
                            or csv_base.lower() == "crm_vendas_config"
                        ):
                            table_name = "crm_vendas_config"
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
                            rows = [_normalize_backup_csv_row_keys(r) for r in rows]
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
                            db_columns = [str(c).strip() for c in db_columns if c is not None and str(c).strip()]
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
                                    and _is_crm_issnet_int_col(c)
                                ):
                                    cols_for_insert.append(c)
                            if table_name == "crm_vendas_config":
                                missing_issnet: List[str] = []
                                for logical in BACKUP_CRM_CONFIG_EXTRA_INT_COLUMNS:
                                    actual = next(
                                        (
                                            dbc
                                            for dbc in db_columns
                                            if (dbc or "").strip().lower() == logical
                                        ),
                                        None,
                                    )
                                    if actual and actual not in cols_for_insert:
                                        missing_issnet.append(actual)
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
                                if (
                                    table_name == "crm_vendas_config"
                                    and not db_helper._is_sqlite()
                                    and _connection_is_postgresql(db_helper.get_connection())
                                ):
                                    _ensure_crm_vendas_config_pg_int_defaults(cursor, qual)
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
                                            nullable, dtype = col_info.get(
                                                col,
                                                col_info.get(
                                                    (col or "").strip(),
                                                    (True, ""),
                                                ),
                                            )
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
                                            and _is_crm_issnet_int_col(col)
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
