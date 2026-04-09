"""
Serviço para gerenciamento de schemas de banco de dados.
Centraliza lógica de criação e configuração de schemas PostgreSQL.

Isolamento por loja:
- Ao criar uma loja (LojaCreateSerializer), é chamado configurar_schema_completo(loja).
- Isso cria um schema PostgreSQL exclusivo (ex: loja_clinica_vida_5889) e aplica as
  migrations nesse schema. Assim o backup e a aplicação usam apenas as tabelas desse
  schema, sem risco de misturar dados de outras lojas ou do superadmin.
"""
import logging
import re
from django.db import connection
from django.conf import settings

logger = logging.getLogger(__name__)

# Apps extras por slug de TipoLoja (única fonte para migrate / auditoria)
TIPO_LOJA_EXTRA_APPS = {
    'clinica-de-estetica': ['clinica_estetica'],
    'clinica-estetica': ['clinica_estetica'],
    'clinica-da-beleza': ['clinica_beleza', 'whatsapp'],
    'e-commerce': ['ecommerce'],
    'restaurante': ['restaurante'],
    'servicos': ['servicos'],
    'cabeleireiro': ['cabeleireiro'],
    'crm-vendas': ['crm_vendas', 'nfse_integration'],
}


def get_apps_esperados_para_loja(loja) -> list[str]:
    """
    Apps cujo schema deve existir para esta loja (alinhado a aplicar_migrations).
    Sempre inclui stores e products.
    """
    tipo_slug = (loja.tipo_loja.slug if loja.tipo_loja else '').strip() or 'unknown'
    base = ['stores', 'products']
    return base + TIPO_LOJA_EXTRA_APPS.get(tipo_slug, [])


class DatabaseSchemaService:
    """
    Serviço responsável por criar e configurar schemas de banco de dados
    """
    
    @staticmethod
    def validar_nome_schema(schema_name: str) -> bool:
        """
        Valida nome do schema para evitar SQL injection
        
        Args:
            schema_name: Nome do schema a ser validado
            
        Returns:
            True se válido
            
        Raises:
            ValueError: Se nome for inválido
        """
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', schema_name):
            raise ValueError(f"Nome de schema inválido: {schema_name}")
        return True
    
    @staticmethod
    def criar_schema(loja) -> bool:
        """
        Cria schema no PostgreSQL para a loja
        
        Args:
            loja: Objeto Loja
            
        Returns:
            True se criado com sucesso
            
        Raises:
            Exception: Se houver erro na criação
        """
        schema_name = loja.database_name.replace('-', '_')
        
        try:
            # Validar nome
            DatabaseSchemaService.validar_nome_schema(schema_name)
            
            # Criar schema
            with connection.cursor() as cursor:
                cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
            
            logger.info(f"Schema '{schema_name}' criado no PostgreSQL")
            
            # Verificar criação
            if not DatabaseSchemaService.verificar_schema_existe(schema_name):
                raise Exception(f"Schema '{schema_name}' não foi criado corretamente!")
            
            logger.info(f"Schema '{schema_name}' verificado e confirmado")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar schema '{schema_name}': {e}")
            raise
    
    @staticmethod
    def verificar_schema_existe(schema_name: str) -> bool:
        """
        Verifica se schema existe no banco
        
        Args:
            schema_name: Nome do schema
            
        Returns:
            True se existe
        """
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.schemata 
                WHERE schema_name = %s
            """, [schema_name])
            return cursor.fetchone()[0] > 0
    

    
    @staticmethod
    def aplicar_migrations(loja) -> bool:
        """
        Aplica migrations no schema da loja executando SQL diretamente.
        
        CORREÇÃO v1016: Django call_command('migrate') ignora search_path COMPLETAMENTE.
        Solução DEFINITIVA: Obter SQL das migrations e executar diretamente no schema.
        
        Args:
            loja: Objeto Loja
            
        Returns:
            True se aplicado com sucesso
        """
        from django.core.management import call_command
        from django.db import connections
        from django.db.migrations.executor import MigrationExecutor
        from io import StringIO
        
        # 1. Adicionar config
        from core.db_config import ensure_loja_database_config
        
        if not ensure_loja_database_config(loja.database_name, conn_max_age=60):
            raise RuntimeError(
                f"Não foi possível adicionar configuração do banco '{loja.database_name}'. "
                "Verifique se DATABASE_URL está definida."
            )
        
        if loja.database_name not in settings.DATABASES:
            raise RuntimeError(f"Config do banco '{loja.database_name}' não encontrada em settings.DATABASES!")
        
        tipo_slug = (loja.tipo_loja.slug if loja.tipo_loja else '').strip() or 'unknown'
        apps_to_migrate = get_apps_esperados_para_loja(loja)
        schema_name = loja.database_name.replace('-', '_')
        
        try:
            conn = connections[loja.database_name]
            conn.ensure_connection()
            
            logger.info(f"🚀 Iniciando migrations manuais para schema '{schema_name}'")
            
            # Criar tabela django_migrations no schema
            with conn.cursor() as cur:
                cur.execute(f'SET search_path TO "{schema_name}", public')
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS django_migrations (
                        id SERIAL PRIMARY KEY,
                        app VARCHAR(255) NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        applied TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                """)
                logger.info(f"✅ Tabela django_migrations criada em '{schema_name}'")
            
            # Para cada app, obter migrations não aplicadas e executar SQL
            for app in apps_to_migrate:
                try:
                    logger.info(f"📦 Processando app: {app}")
                    
                    # Obter migrations não aplicadas
                    with conn.cursor() as cur:
                        cur.execute(f'SET search_path TO "{schema_name}", public')
                        cur.execute(
                            "SELECT name FROM django_migrations WHERE app = %s",
                            [app]
                        )
                        applied = {row[0] for row in cur.fetchall()}
                    
                    # Obter TODAS as migrations do app (não apenas leaf nodes)
                    from django.db.migrations.loader import MigrationLoader
                    loader = MigrationLoader(conn)
                    
                    # Obter todas as migrations do app na ordem correta
                    migrations_to_apply = []
                    if app in loader.migrated_apps:
                        # Obter plan de execução completo
                        from django.db.migrations.executor import MigrationExecutor
                        executor = MigrationExecutor(conn)
                        
                        # Obter todas as migrations do app
                        app_migrations = [
                            key for key in loader.graph.nodes 
                            if key[0] == app and key[1] not in applied
                        ]
                        
                        # Ordenar usando o grafo de dependências
                        if app_migrations:
                            plan = []
                            for migration_key in app_migrations:
                                # Adicionar migration e suas dependências
                                try:
                                    migration_plan = executor.loader.graph.forwards_plan(migration_key)
                                    for mig in migration_plan:
                                        if mig[0] == app and mig[1] not in applied and mig not in plan:
                                            plan.append(mig)
                                except Exception as e:
                                    logger.warning(f"      ⚠️  Erro ao obter plan para {migration_key}: {e}")
                            
                            migrations_to_apply = plan
                    
                    # Se não conseguiu obter via plan, usar ordenação simples
                    if not migrations_to_apply:
                        migrations_to_apply = [
                            key for key in loader.graph.nodes 
                            if key[0] == app and key[1] not in applied
                        ]
                        migrations_to_apply = sorted(migrations_to_apply, key=lambda x: x[1])
                    
                    if not migrations_to_apply:
                        logger.info(f"   ℹ️  Nenhuma migration pendente para {app}")
                        continue
                    
                    logger.info(f"   📝 {len(migrations_to_apply)} migration(s) pendente(s)")
                    
                    # Executar cada migration
                    for app_label, migration_name in migrations_to_apply:
                        try:
                            # Obter SQL da migration
                            sql_out = StringIO()
                            call_command(
                                'sqlmigrate',
                                app_label,
                                migration_name,
                                '--database', loja.database_name,
                                stdout=sql_out
                            )
                            sql = sql_out.getvalue()
                            
                            if not sql or sql.strip() == '--':
                                logger.info(f"      ⚠️  Migration {migration_name} sem SQL")
                                # Registrar como aplicada mesmo assim
                                with conn.cursor() as cur:
                                    cur.execute(f'SET search_path TO "{schema_name}", public')
                                    cur.execute(
                                        "INSERT INTO django_migrations (app, name, applied) VALUES (%s, %s, NOW())",
                                        [app_label, migration_name]
                                    )
                                continue
                            
                            # Executar SQL no schema
                            with conn.cursor() as cur:
                                cur.execute(f'SET search_path TO "{schema_name}", public')
                                cur.execute(sql)
                                
                                # Registrar migration como aplicada
                                cur.execute(
                                    "INSERT INTO django_migrations (app, name, applied) VALUES (%s, %s, NOW())",
                                    [app_label, migration_name]
                                )
                            
                            logger.info(f"      ✅ {migration_name}")
                            
                        except Exception as e:
                            logger.error(f"      ❌ Erro em {migration_name}: {e}")
                            if tipo_slug == 'crm-vendas' and app == 'crm_vendas':
                                raise
                    
                    logger.info(f"   ✅ App {app} concluído")
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao processar app {app}: {e}")
                    if tipo_slug == 'crm-vendas' and app == 'crm_vendas':
                        raise
                    logger.warning(f"Continuando apesar do erro em {app}")
            
            # Verificar se tabelas foram criadas
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = %s 
                    AND table_type = 'BASE TABLE' 
                    AND table_name NOT LIKE 'django_%%'
                    """,
                    [schema_name]
                )
                tabelas_count = cur.fetchone()[0]
                
                if tabelas_count == 0:
                    logger.error(
                        f"❌ ERRO CRÍTICO: Schema '{schema_name}' está VAZIO após migrations! "
                        f"Apps tentados: {apps_to_migrate}."
                    )
                    
                    raise RuntimeError(
                        f"Schema '{schema_name}' está vazio após migrations. "
                        "As tabelas não foram criadas no schema correto. "
                        "Entre em contato com o suporte técnico."
                    )
                else:
                    logger.info(
                        f"✅ Schema '{schema_name}' criado com sucesso: {tabelas_count} tabela(s)"
                    )
            
            logger.info(f"🎉 Migrations concluídas para '{loja.database_name}'")
            return True
        except Exception as e:
            logger.error(f"Erro ao aplicar migrations: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    @staticmethod
    def _mover_tabelas_public_para_schema(loja, schema_name: str, apps_to_migrate: list) -> None:
        """
        Fallback: se migrate criou tabelas em public, move-as para o schema da loja.
        
        CORREÇÃO v983: Melhorado para ser mais robusto e informativo.
        """
        from django.db import connections
        try:
            DatabaseSchemaService.validar_nome_schema(schema_name)
        except ValueError:
            logger.warning(f"Nome de schema inválido: {schema_name}")
            return
        
        app_prefixes = [f"{app}_" for app in apps_to_migrate]
        
        try:
            conn = connections[loja.database_name]
            conn.ensure_connection()
            with conn.cursor() as cur:
                # Verificar se schema já tem tabelas (não precisa mover)
                cur.execute(
                    """
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = %s 
                    AND table_type = 'BASE TABLE' 
                    AND table_name NOT LIKE 'django_%%'
                    """,
                    [schema_name],
                )
                if cur.fetchone()[0] > 0:
                    logger.info(f"Schema '{schema_name}' já possui tabelas, não precisa mover")
                    return
                
                # Buscar tabelas em public que pertencem aos apps da loja
                cur.execute(
                    """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE' 
                    ORDER BY table_name
                    """
                )
                todas = [r[0] for r in cur.fetchall()]
                tabelas_mover = [t for t in todas if any(t.startswith(p) for p in app_prefixes)]
                
                if not tabelas_mover:
                    logger.warning(
                        f"⚠️  Nenhuma tabela encontrada em 'public' para mover para '{schema_name}'. "
                        f"Apps esperados: {apps_to_migrate}"
                    )
                    return
                
                logger.info(
                    f"🔄 Fallback ativado: movendo {len(tabelas_mover)} tabela(s) "
                    f"de 'public' para '{schema_name}'"
                )
                
                # Mover django_migrations primeiro (se existir)
                cur.execute(
                    """
                    SELECT EXISTS (
                        SELECT 1 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'django_migrations'
                    )
                    """
                )
                
                if cur.fetchone()[0]:
                    # Buscar migrations dos apps da loja
                    cur.execute(
                        "SELECT app, name, applied FROM public.django_migrations WHERE app = ANY(%s)",
                        [apps_to_migrate]
                    )
                    migracoes = cur.fetchall()
                    
                    if migracoes:
                        # Criar tabela django_migrations no schema
                        cur.execute(
                            f'''
                            CREATE TABLE IF NOT EXISTS "{schema_name}".django_migrations (
                                id SERIAL PRIMARY KEY,
                                app VARCHAR(255) NOT NULL,
                                name VARCHAR(255) NOT NULL,
                                applied TIMESTAMPTZ NOT NULL
                            )
                            '''
                        )
                        
                        # Copiar migrations
                        for app, name, applied in migracoes:
                            cur.execute(
                                f'INSERT INTO "{schema_name}".django_migrations (app, name, applied) VALUES (%s, %s, %s)',
                                [app, name, applied]
                            )
                        
                        # Remover de public
                        cur.execute(
                            "DELETE FROM public.django_migrations WHERE app = ANY(%s)",
                            [apps_to_migrate]
                        )
                        
                        logger.info(f"✅ {len(migracoes)} migration(s) movida(s) para '{schema_name}'")
                
                # Mover tabelas
                tabelas_movidas = 0
                for table_name in tabelas_mover:
                    if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
                        try:
                            cur.execute(f'ALTER TABLE public."{table_name}" SET SCHEMA "{schema_name}"')
                            tabelas_movidas += 1
                            logger.info(f"✅ Tabela {table_name} movida para {schema_name}")
                        except Exception as e:
                            logger.error(f"❌ Erro ao mover {table_name}: {e}")
                    else:
                        logger.warning(f"⚠️  Nome de tabela inválido (ignorado): {table_name}")
                
                logger.info(
                    f"✅ Fallback concluído: {tabelas_movidas}/{len(tabelas_mover)} tabela(s) "
                    f"movida(s) para '{schema_name}'"
                )
                
        except Exception as e:
            logger.error(f"❌ Erro no fallback de movimentação de tabelas: {e}")
            import traceback
            logger.error(traceback.format_exc())

    @staticmethod
    def configurar_schema_completo(loja) -> bool:
        """
        Executa todo o processo de configuração do schema individual da loja.
        Deve ser chamado na criação da loja para garantir banco/schema isolado
        e evitar que o backup exporte dados de outras lojas ou do superadmin.

        Passos: criar schema -> marcar database_created -> aplicar migrations.

        Args:
            loja: Objeto Loja

        Returns:
            True se configurado com sucesso
        """
        try:
            # 1. Criar schema
            DatabaseSchemaService.criar_schema(loja)
            
            # 2. Marcar como criado
            loja.database_created = True
            loja.save()
            
            # 3. Aplicar migrations (já adiciona configuração Django internamente)
            if not DatabaseSchemaService.aplicar_migrations(loja):
                tipo_slug = (loja.tipo_loja.slug if loja.tipo_loja else '').strip() or 'unknown'
                raise RuntimeError(
                    f"Falha ao aplicar migrations no schema da loja (tipo: {tipo_slug}). "
                    "O cadastro não pode ser concluído sem as tabelas do app."
                )
            return True
        except Exception:
            logger.exception("configurar_schema_completo")
            raise
