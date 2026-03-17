"""
Comando para detectar e limpar dados órfãos no sistema.

Verifica:
1. Arquivos de banco SQLite sem loja correspondente
2. Schemas PostgreSQL sem loja correspondente
3. Usuários sem lojas (órfãos)
4. Sessões de usuários inexistentes
5. Dados em tabelas com loja_id inválido
6. Configurações de banco em settings.DATABASES sem loja

Uso:
    python manage.py limpar_orfaos --dry-run  # Apenas listar
    python manage.py limpar_orfaos --execute  # Executar limpeza
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection, transaction
from django.contrib.auth import get_user_model
import os
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Detecta e remove dados órfãos (arquivos, schemas, usuários, sessões)'

    def _delete_user_raw(self, user_id):
        """
        Remove usuário via SQL (evita stores_store inexistente).
        Ordem: deletar FKs antes de auth_user.
        """
        with connection.cursor() as cursor:
            # Tabelas que referenciam auth_user (deletar antes de auth_user)
            tabelas_user_fk = [
                'superadmin_historico_acesso_global',
                'notificacoes_notification',
                'push_pushsubscription',
            ]
            for tabela in tabelas_user_fk:
                try:
                    cursor.execute(
                        f'DELETE FROM {tabela} WHERE user_id = %s',
                        [user_id]
                    )
                except Exception:
                    pass  # Tabela pode não existir (ex: app não migrado)
            cursor.execute('DELETE FROM auth_user_groups WHERE user_id = %s', [user_id])
            cursor.execute(
                'DELETE FROM auth_user_user_permissions WHERE user_id = %s',
                [user_id]
            )
            cursor.execute('DELETE FROM auth_user WHERE id = %s', [user_id])

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas listar órfãos sem remover',
        )
        parser.add_argument(
            '--execute',
            action='store_true',
            help='Executar limpeza de órfãos',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        execute = options['execute']

        if not dry_run and not execute:
            self.stdout.write(
                self.style.ERROR('❌ Use --dry-run para listar ou --execute para limpar')
            )
            return

        mode = '🔍 MODO ANÁLISE (dry-run)' if dry_run else '🗑️ MODO EXECUÇÃO'
        self.stdout.write(self.style.WARNING(f'\n{mode}\n'))

        # Importar modelos
        from superadmin.models import Loja, UserSession, ProfissionalUsuario, VendedorUsuario

        # 1. Verificar arquivos SQLite órfãos
        self.stdout.write(self.style.HTTP_INFO('\n1️⃣ Verificando arquivos SQLite órfãos...'))
        lojas_db_names = set(Loja.objects.values_list('database_name', flat=True))
        arquivos_orfaos = []

        for filename in os.listdir(settings.BASE_DIR):
            if filename.startswith('db_loja_') and filename.endswith('.sqlite3'):
                db_name = filename.replace('db_', '').replace('.sqlite3', '')
                if db_name not in lojas_db_names and db_name != 'loja_template':
                    arquivos_orfaos.append(filename)

        if arquivos_orfaos:
            self.stdout.write(self.style.WARNING(f'   ⚠️ Encontrados {len(arquivos_orfaos)} arquivos órfãos:'))
            for arquivo in arquivos_orfaos:
                self.stdout.write(f'      - {arquivo}')
                if execute:
                    try:
                        os.remove(settings.BASE_DIR / arquivo)
                        self.stdout.write(self.style.SUCCESS(f'         ✅ Removido'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'         ❌ Erro: {e}'))
        else:
            self.stdout.write(self.style.SUCCESS('   ✅ Nenhum arquivo SQLite órfão'))

        # 2. Verificar schemas PostgreSQL órfãos
        self.stdout.write(self.style.HTTP_INFO('\n2️⃣ Verificando schemas PostgreSQL órfãos...'))
        DATABASE_URL = os.environ.get('DATABASE_URL', '')
        
        if 'postgres' in DATABASE_URL.lower():
            lojas_schemas = set(
                loja.database_name.replace('-', '_') 
                for loja in Loja.objects.all()
            )
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name LIKE 'loja_%'
                    AND schema_name NOT IN ('public', 'information_schema')
                """)
                schemas_existentes = [row[0] for row in cursor.fetchall()]
            
            schemas_orfaos = [s for s in schemas_existentes if s not in lojas_schemas]
            
            if schemas_orfaos:
                self.stdout.write(self.style.WARNING(f'   ⚠️ Encontrados {len(schemas_orfaos)} schemas órfãos:'))
                for schema in schemas_orfaos:
                    self.stdout.write(f'      - {schema}')
                    if execute:
                        try:
                            with connection.cursor() as cursor:
                                cursor.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
                            self.stdout.write(self.style.SUCCESS(f'         ✅ Removido'))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'         ❌ Erro: {e}'))
            else:
                self.stdout.write(self.style.SUCCESS('   ✅ Nenhum schema PostgreSQL órfão'))
        else:
            self.stdout.write(self.style.SUCCESS('   ℹ️ Não está usando PostgreSQL'))

        # 3. Verificar usuários órfãos (sem lojas)
        self.stdout.write(self.style.HTTP_INFO('\n3️⃣ Verificando usuários órfãos...'))
        usuarios_com_loja = set(Loja.objects.values_list('owner_id', flat=True))
        usuarios_prof = set(ProfissionalUsuario.objects.values_list('user_id', flat=True))
        usuarios_vend = set(VendedorUsuario.objects.values_list('user_id', flat=True))
        usuarios_validos = usuarios_com_loja | usuarios_prof | usuarios_vend
        usuarios_orfaos = User.objects.exclude(
            id__in=usuarios_validos
        ).exclude(
            is_superuser=True
        ).exclude(
            is_staff=True
        )

        if usuarios_orfaos.exists():
            self.stdout.write(self.style.WARNING(f'   ⚠️ Encontrados {usuarios_orfaos.count()} usuários órfãos:'))
            # Coletar IDs antes de iterar (evita lazy eval que pode tocar stores_store)
            user_ids = list(usuarios_orfaos.values_list('id', flat=True))
            user_info = {u.id: (u.username, u.email) for u in usuarios_orfaos}
            for user_id in user_ids:
                username, email = user_info.get(user_id, ('?', '?'))
                self.stdout.write(f'      - {username} (ID: {user_id}, Email: {email})')
                if execute:
                    try:
                        # Usar SQL direto para evitar user.delete() que acessa stores_store
                        # (app stores legado; sistema usa superadmin.Loja)
                        UserSession.objects.filter(user_id=user_id).delete()
                        ProfissionalUsuario.objects.filter(user_id=user_id).delete()
                        VendedorUsuario.objects.filter(user_id=user_id).delete()
                        self._delete_user_raw(user_id)
                        self.stdout.write(self.style.SUCCESS(f'         ✅ Removido'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'         ❌ Erro: {e}'))
        else:
            self.stdout.write(self.style.SUCCESS('   ✅ Nenhum usuário órfão'))

        # 4. Verificar sessões de usuários inexistentes
        self.stdout.write(self.style.HTTP_INFO('\n4️⃣ Verificando sessões órfãs...'))
        usuarios_ids = set(User.objects.values_list('id', flat=True))
        sessoes_orfas = UserSession.objects.exclude(user_id__in=usuarios_ids)

        if sessoes_orfas.exists():
            count = sessoes_orfas.count()
            self.stdout.write(self.style.WARNING(f'   ⚠️ Encontradas {count} sessões órfãs'))
            if execute:
                sessoes_orfas.delete()
                self.stdout.write(self.style.SUCCESS(f'      ✅ {count} sessões removidas'))
        else:
            self.stdout.write(self.style.SUCCESS('   ✅ Nenhuma sessão órfã'))

        # 5. Verificar ProfissionalUsuario órfãos
        self.stdout.write(self.style.HTTP_INFO('\n5️⃣ Verificando ProfissionalUsuario órfãos...'))
        prof_usuarios_orfaos = ProfissionalUsuario.objects.exclude(user_id__in=usuarios_ids)

        if prof_usuarios_orfaos.exists():
            count = prof_usuarios_orfaos.count()
            self.stdout.write(self.style.WARNING(f'   ⚠️ Encontrados {count} ProfissionalUsuario órfãos'))
            if execute:
                prof_usuarios_orfaos.delete()
                self.stdout.write(self.style.SUCCESS(f'      ✅ {count} registros removidos'))
        else:
            self.stdout.write(self.style.SUCCESS('   ✅ Nenhum ProfissionalUsuario órfão'))

        # 6. Verificar configurações de banco órfãs em settings.DATABASES
        self.stdout.write(self.style.HTTP_INFO('\n6️⃣ Verificando configurações de banco órfãs...'))
        lojas_db_names_set = set(Loja.objects.values_list('database_name', flat=True))
        configs_orfas = []

        for db_name in list(settings.DATABASES.keys()):
            if db_name.startswith('loja_') and db_name not in ['default', 'suporte', 'loja_template']:
                if db_name not in lojas_db_names_set:
                    configs_orfas.append(db_name)

        if configs_orfas:
            self.stdout.write(self.style.WARNING(f'   ⚠️ Encontradas {len(configs_orfas)} configurações órfãs:'))
            for db_name in configs_orfas:
                self.stdout.write(f'      - {db_name}')
                if execute:
                    try:
                        del settings.DATABASES[db_name]
                        self.stdout.write(self.style.SUCCESS(f'         ✅ Removido do settings'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'         ❌ Erro: {e}'))
        else:
            self.stdout.write(self.style.SUCCESS('   ✅ Nenhuma configuração órfã'))

        # 7. Verificar dados em tabelas com loja_id inválido (safety net)
        self.stdout.write(self.style.HTTP_INFO('\n7️⃣ Verificando dados com loja_id inválido...'))
        lojas_ids = set(Loja.objects.values_list('id', flat=True))
        
        # Tabelas a verificar (do orfaos_config.py)
        from superadmin.orfaos_config import TABELAS_LOJA_ID_DEFAULT
        
        total_orfaos = 0
        for tabela, coluna in TABELAS_LOJA_ID_DEFAULT:
            try:
                with connection.cursor() as cursor:
                    # Contar registros com loja_id inválido
                    cursor.execute(f"""
                        SELECT COUNT(*) FROM {tabela} 
                        WHERE {coluna} NOT IN %s
                    """, [tuple(lojas_ids) if lojas_ids else (0,)])
                    count = cursor.fetchone()[0]
                    
                    if count > 0:
                        total_orfaos += count
                        self.stdout.write(self.style.WARNING(f'   ⚠️ {tabela}: {count} registros órfãos'))
                        
                        if execute:
                            cursor.execute(f"""
                                DELETE FROM {tabela} 
                                WHERE {coluna} NOT IN %s
                            """, [tuple(lojas_ids) if lojas_ids else (0,)])
                            self.stdout.write(self.style.SUCCESS(f'      ✅ {count} registros removidos'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Erro em {tabela}: {e}'))

        if total_orfaos == 0:
            self.stdout.write(self.style.SUCCESS('   ✅ Nenhum dado com loja_id inválido'))

        # Resumo final
        self.stdout.write(self.style.HTTP_INFO('\n' + '='*60))
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 Análise concluída. Use --execute para limpar.'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ Limpeza concluída!'))
        self.stdout.write(self.style.HTTP_INFO('='*60 + '\n'))
