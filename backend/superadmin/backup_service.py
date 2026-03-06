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
import zipfile
import io
import os
import re
import logging
from typing import Dict, List, Optional, Tuple
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
    'clinica-de-estetica': ('stores_', 'products_', 'clinica_'),  # clinica_* da app clinica_estetica
    'clinica-da-beleza': ('stores_', 'products_', 'clinica_beleza_', 'whatsapp_'),
    'crm-vendas': ('stores_', 'products_', 'crm_'),
    'e-commerce': ('stores_', 'products_', 'ecommerce_'),
    'restaurante': ('stores_', 'products_', 'restaurante_'),
    'servicos': ('stores_', 'products_', 'servicos_'),
    'cabeleireiro': ('stores_', 'products_', 'cabeleireiro_'),
}
# Prefixos a excluir por tipo de app (ex.: clinica_beleza_ não é da clínica de estética)
BACKUP_TIPO_APP_EXCLUDED_PREFIXES = {
    'clinica-de-estetica': ('clinica_beleza_',),
}
# Regex para validar nome de tabela/coluna (segurança SQL: apenas alfanumérico e underscore)
BACKUP_SAFE_IDENTIFIER_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')


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
        if not (self._pg_schema and BACKUP_SAFE_IDENTIFIER_RE.match(self._pg_schema)):
            return table_name
        return f'"{self._pg_schema}"."{table_name}"'
    
    def qualified_table_name(self, table_name: str) -> str:
        """Nome da tabela qualificado com schema (PostgreSQL) ou só o nome (SQLite). Uso em SQL."""
        return self._qualified_table(table_name)
    
    def ensure_pg_schema_exists(self) -> bool:
        """Cria o schema no PostgreSQL se não existir (usa a conexão da loja). Retorna True se OK."""
        if self._is_sqlite() or not self._pg_schema or not BACKUP_SAFE_IDENTIFIER_RE.match(self._pg_schema):
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
            cursor.execute(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
                """,
                [self._pg_schema, table_name]
            )
            return [row[0] for row in cursor.fetchall()]
    
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
            if not db_helper._is_sqlite() and db_helper._pg_schema and BACKUP_SAFE_IDENTIFIER_RE.match(db_helper._pg_schema):
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

            # Se o schema não tem tabelas: garantir que o schema existe (PostgreSQL), aplicar migrations e listar de novo
            if not table_names and loja.database_created:
                try:
                    from .services.database_schema_service import DatabaseSchemaService
                    logger.info(f"🔄 Schema vazio - garantindo schema e aplicando migrations para loja {loja.nome} (ID: {loja_id})")
                    db_helper.ensure_pg_schema_exists()
                    if DatabaseSchemaService.aplicar_migrations(loja):
                        table_names = db_helper.get_all_table_names()
                        if table_names:
                            logger.info(f"✅ Migrations aplicadas - {len(table_names)} tabela(s) encontrada(s)")
                except Exception as e:
                    logger.warning(f"⚠️ Falha ao aplicar migrations antes do backup: {e}")

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
            # Buscar loja
            loja = Loja.objects.get(id=loja_id)
            
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
                # Ler metadados
                try:
                    import json
                    metadata_content = zip_file.read('_metadata.json')
                    metadata = json.loads(metadata_content)
                    logger.info(f"📋 Metadados do backup: {metadata.get('data_backup')}")
                except KeyError:
                    logger.warning("⚠️ Arquivo de metadados não encontrado no backup")
                    metadata = {}
                
                # Inicializar helper
                db_helper = DatabaseHelper(loja.database_name)
                
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
                
                with transaction.atomic(using=loja.database_name):
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
                            
                            # Colunas da tabela no banco (ordem e nomes)
                            db_columns = db_helper.get_table_columns(table_name)
                            if not db_columns:
                                logger.warning(f"⚠️ Não foi possível obter colunas da tabela {table_name}")
                                continue
                            
                            # Usar apenas colunas que existem no CSV e na tabela (ordem da tabela)
                            # Filtrar também por nome seguro (defesa em profundidade)
                            csv_headers = list(rows[0].keys()) if rows else []
                            cols_for_insert = [
                                c for c in db_columns
                                if c in csv_headers and DatabaseHelper.is_safe_table_name(c)
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
                                        val = row.get(col, "")
                                        if val == "" and col != "id":
                                            values.append(None)
                                        else:
                                            values.append(val)
                                    cursor.execute(insert_sql, values)
                            
                            count = len(rows)
                            total_registros += count
                            tabelas_stats[table_name] = count
                            
                            logger.info(f"✅ Tabela {table_name}: {count} registros importados")
                        
                        except Exception as e:
                            logger.error(f"❌ Erro ao importar tabela {table_name}: {e}")
                            raise BackupImportError(f"Erro ao importar {table_name}: {str(e)}")
                
                logger.info(f"✅ Importação concluída - {total_registros} registros importados")
                
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
