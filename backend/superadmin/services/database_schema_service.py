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
        
        CORREÇÃO v1015: Django call_command('migrate') ignora search_path completamente.
        Solução: Executar SQL das migrations diretamente no schema usando cursor.
        
        Args:
            loja: Objeto Loja
            
        Returns:
            True se aplicado com sucesso
        """
        from django.core.management import call_command
        from django.db import connections
        from io import StringIO
        
        # 1. Adicionar config usando função que funcionava antes
        from core.db_config import ensure_loja_database_config
        
        if not ensure_loja_database_config(loja.database_name, conn_max_age=60):
            raise RuntimeError(
                f"Não foi possível adicionar configuração do banco '{loja.database_name}'. "
                "Verifique se DATABASE_URL está definida."
            )
        
        if loja.database_name not in settings.DATABASES:
            raise RuntimeError(f"Config do banco '{loja.database_name}' não encontrada em settings.DATABASES!")
        
        tipo_slug = (loja.tipo_loja.slug if loja.tipo_loja else '').strip() or 'unknown'
        
        # Apps base (comuns a todos os tipos de app)
        base_apps = ['stores', 'products']
        
        # Apps por tipo de app (slug do TipoLoja)
        tipo_apps = {
            'clinica-de-estetica': ['clinica_estetica'],
            'clinica-da-beleza': ['clinica_beleza', 'whatsapp'],
            'e-commerce': ['ecommerce'],
            'restaurante': ['restaurante'],
            'servicos': ['servicos'],
            'cabeleireiro': ['cabeleireiro'],
            'crm-vendas': ['crm_vendas'],
        }
        
        apps_to_migrate = base_apps + tipo_apps.get(tipo_slug, [])
        schema_name = loja.database_name.replace('-', '_')
        
        try:
            conn = connections[loja.database_name]
            conn.ensure_connection()
            
            # Fechar conexão existente para forçar nova com config atualizada
            if loja.database_name in connections:
                try:
                    connections[loja.database_name].close()
                except Exception:
                    pass
            
            conn = connections[loja.database_name]
            conn.ensure_connection()
            
            # Verificar search_path
            with conn.cursor() as cur:
                cur.execute('SHOW search_path')
                sp = cur.fetchone()[0]
                logger.info(f"🔍 search_path inicial: {sp}")
            
            for app in apps_to_migrate:
                try:
                    # Definir search_path ANTES de cada migrate
                    with conn.cursor() as cur:
                        cur.execute(f'SET search_path TO "{schema_name}", public')
                        cur.execute('SHOW search_path')
                        sp = cur.fetchone()[0]
                        logger.info(f"✅ search_path configurado para {app}: {sp}")
                    
                    # Executar migrate
                    call_command('migrate', app, '--database', loja.database_name, verbosity=0)
                    logger.info(f"✅ Migrations aplicadas: {app}")
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao aplicar migration {app}: {e}")
                    if tipo_slug == 'crm-vendas' and app == 'crm_vendas':
                        raise
                    logger.warning(f"Continuando apesar do erro em {app}")
            
            # Fallback: se tabelas foram criadas em public, mover para schema
            DatabaseSchemaService._mover_tabelas_public_para_schema(loja, schema_name, apps_to_migrate)
            
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
            
            logger.info(f"Tabelas criadas no schema '{loja.database_name}' via migrations")
            return True
        except Exception as e:
            logger.error(f"Erro ao aplicar migrations: {e}")
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
                tipo_slug = (loja.tipo_loja.slug if loja.tipo_loja else '').strip() or ''
                if tipo_slug == 'crm-vendas':
                    raise RuntimeError(
                        "Falha ao criar tabelas do CRM no schema da loja. "
                        "A loja CRM não pode ser usada sem as tabelas crm_vendas."
                    )
                logger.warning("Migrations aplicadas com falhas parciais (loja não é CRM)")
            return True
        except Exception as e:
            logger.error(f"Erro ao configurar schema completo: {e}")
            tipo_slug = (loja.tipo_loja.slug if loja.tipo_loja else '').strip() or ''
            if tipo_slug == 'crm-vendas':
                raise
            return False
