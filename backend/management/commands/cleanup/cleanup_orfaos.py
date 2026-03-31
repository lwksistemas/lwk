"""
Management command para limpar dados órfãos do sistema
Remove: schemas órfãos, lojas vazias, usuários sem lojas
Migrado de: backend/limpar_orfaos_completo.py
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.contrib.auth.models import User
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Limpa dados órfãos do sistema (schemas, lojas vazias, usuários)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostrar o que seria removido, sem executar',
        )
        parser.add_argument(
            '--schemas',
            action='store_true',
            help='Limpar apenas schemas órfãos',
        )
        parser.add_argument(
            '--lojas',
            action='store_true',
            help='Limpar apenas lojas vazias',
        )
        parser.add_argument(
            '--usuarios',
            action='store_true',
            help='Limpar apenas usuários órfãos',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        only_schemas = options['schemas']
        only_lojas = options['lojas']
        only_usuarios = options['usuarios']
        
        # Se nenhuma opção específica, fazer tudo
        do_all = not (only_schemas or only_lojas or only_usuarios)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 Modo DRY-RUN: Nenhuma alteração será feita\n'))
        
        self.stdout.write(self.style.SUCCESS('🧹 Iniciando limpeza de órfãos...\n'))
        
        total_removidos = 0
        
        # 1. Schemas órfãos
        if do_all or only_schemas:
            schemas_orfaos = self._find_orphan_schemas()
            if dry_run:
                self.stdout.write(f'📋 Schemas órfãos encontrados: {len(schemas_orfaos)}')
                for schema in schemas_orfaos[:10]:
                    self.stdout.write(f'   - {schema}')
                if len(schemas_orfaos) > 10:
                    self.stdout.write(f'   ... e mais {len(schemas_orfaos) - 10}')
            else:
                removidos = self._cleanup_orphan_schemas(schemas_orfaos)
                total_removidos += removidos
        
        # 2. Lojas vazias
        if do_all or only_lojas:
            lojas_vazias = self._find_empty_lojas()
            if dry_run:
                self.stdout.write(f'\n📋 Lojas vazias encontradas: {len(lojas_vazias)}')
                for loja_id, slug, nome, schema in lojas_vazias[:10]:
                    self.stdout.write(f'   - {slug} (ID: {loja_id})')
                if len(lojas_vazias) > 10:
                    self.stdout.write(f'   ... e mais {len(lojas_vazias) - 10}')
            else:
                removidos = self._cleanup_empty_lojas(lojas_vazias)
                total_removidos += removidos
        
        # 3. Usuários órfãos
        if do_all or only_usuarios:
            usuarios_orfaos = self._find_orphan_users()
            if dry_run:
                self.stdout.write(f'\n📋 Usuários órfãos encontrados: {len(usuarios_orfaos)}')
                for user_id, username, email in usuarios_orfaos[:10]:
                    self.stdout.write(f'   - {username} ({email})')
                if len(usuarios_orfaos) > 10:
                    self.stdout.write(f'   ... e mais {len(usuarios_orfaos) - 10}')
            else:
                removidos = self._cleanup_orphan_users(usuarios_orfaos)
                total_removidos += removidos
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  Nenhuma alteração foi feita (dry-run)'))
            self.stdout.write('Execute sem --dry-run para aplicar as mudanças')
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\n✅ Limpeza concluída! Total removido: {total_removidos}')
            )
    
    def _find_orphan_schemas(self):
        """Encontra schemas órfãos (sem loja correspondente)"""
        with connection.cursor() as cursor:
            # Schemas que começam com loja_
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name LIKE 'loja_%'
                ORDER BY schema_name
            """)
            all_schemas = [row[0] for row in cursor.fetchall()]
        
        # Schemas de lojas existentes
        lojas = Loja.objects.all()
        valid_schemas = {f'loja_{loja.id}' for loja in lojas}
        
        # Órfãos = schemas sem loja
        orphan_schemas = [s for s in all_schemas if s not in valid_schemas]
        
        return orphan_schemas
    
    def _find_empty_lojas(self):
        """Encontra lojas com schemas vazios"""
        empty_lojas = []
        
        for loja in Loja.objects.all():
            schema = f'loja_{loja.id}'
            
            try:
                with connection.cursor() as cursor:
                    # Verificar se schema existe
                    cursor.execute(f"""
                        SELECT COUNT(*) 
                        FROM information_schema.schemata 
                        WHERE schema_name = '{schema}'
                    """)
                    exists = cursor.fetchone()[0] > 0
                    
                    if not exists:
                        empty_lojas.append((loja.id, loja.slug, loja.nome, schema))
            except Exception:
                pass
        
        return empty_lojas
    
    def _find_orphan_users(self):
        """Encontra usuários órfãos (sem lojas)"""
        orphan_users = []
        
        for user in User.objects.filter(is_superuser=False, is_staff=False):
            # Verificar se tem lojas
            if not user.lojas_owned.exists():
                orphan_users.append((user.id, user.username, user.email))
        
        return orphan_users
    
    def _cleanup_orphan_schemas(self, schemas):
        """Remove schemas órfãos"""
        if not schemas:
            self.stdout.write('✅ Nenhum schema órfão para remover')
            return 0
        
        self.stdout.write(f'\n🗑️  Removendo {len(schemas)} schema(s) órfão(s)...')
        
        removidos = 0
        for schema in schemas:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
                self.stdout.write(self.style.SUCCESS(f'   ✅ Schema removido: {schema}'))
                removidos += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Erro ao remover {schema}: {e}'))
        
        return removidos
    
    def _cleanup_empty_lojas(self, lojas):
        """Remove lojas vazias"""
        if not lojas:
            self.stdout.write('✅ Nenhuma loja vazia para remover')
            return 0
        
        self.stdout.write(f'\n🗑️  Removendo {len(lojas)} loja(s) vazia(s)...')
        
        removidos = 0
        for loja_id, slug, nome, schema in lojas:
            try:
                loja = Loja.objects.get(id=loja_id)
                
                # Remover schema
                with connection.cursor() as cursor:
                    cursor.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
                
                # Remover loja
                loja.delete()
                
                self.stdout.write(self.style.SUCCESS(f'   ✅ Loja removida: {slug} (ID: {loja_id})'))
                removidos += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Erro ao remover loja {slug}: {e}'))
        
        return removidos
    
    def _cleanup_orphan_users(self, usuarios):
        """Remove usuários órfãos"""
        if not usuarios:
            self.stdout.write('✅ Nenhum usuário órfão para remover')
            return 0
        
        self.stdout.write(f'\n🗑️  Removendo {len(usuarios)} usuário(s) órfão(s)...')
        
        removidos = 0
        for user_id, username, email in usuarios:
            try:
                user = User.objects.get(id=user_id)
                
                # Verificar novamente se não tem lojas
                if user.lojas_owned.exists():
                    self.stdout.write(self.style.WARNING(f'   ⚠️  Pulando {username} (tem lojas)'))
                    continue
                
                user.delete()
                self.stdout.write(self.style.SUCCESS(f'   ✅ Usuário removido: {username} ({email})'))
                removidos += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Erro ao remover usuário {username}: {e}'))
        
        return removidos
