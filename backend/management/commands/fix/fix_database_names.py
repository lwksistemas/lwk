"""
Management command para corrigir database_names duplicados
"""
from django.core.management.base import BaseCommand
from django.db import connection
from superadmin.models import Loja
from collections import Counter, defaultdict
import re


class Command(BaseCommand):
    help = 'Corrige database_names duplicados e garante isolamento de dados'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Apenas verificar duplicados sem corrigir',
        )
        parser.add_argument(
            '--auto-confirm',
            action='store_true',
            help='Executar sem pedir confirmação (use com cuidado!)',
        )
    
    def handle(self, *args, **options):
        check_only = options['check_only']
        auto_confirm = options['auto_confirm']
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('🔍 VERIFICANDO DATABASE_NAMES DUPLICADOS'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
        
        # Verificar duplicados
        lojas_problematicas = self._verificar_duplicados()
        
        if not lojas_problematicas:
            self.stdout.write(self.style.SUCCESS('\n✅ Nenhum database_name duplicado encontrado!'))
            return
        
        if check_only:
            self.stdout.write(self.style.WARNING(f'\n⚠️  Encontrados problemas em {len(lojas_problematicas)} lojas'))
            self.stdout.write('Use sem --check-only para corrigir')
            return
        
        # Corrigir
        self._corrigir_todas(lojas_problematicas, auto_confirm)
    
    def _verificar_duplicados(self):
        lojas = Loja.objects.filter(is_active=True)
        database_names = [loja.database_name for loja in lojas]
        duplicados = {name: count for name, count in Counter(database_names).items() if count > 1}
        
        if not duplicados:
            return []
        
        self.stdout.write(self.style.ERROR(f'❌ Encontrados {len(duplicados)} database_names duplicados:\n'))
        
        lojas_problematicas = []
        for db_name, count in duplicados.items():
            self.stdout.write(self.style.ERROR(f'🔴 {db_name} (usado por {count} lojas):'))
            lojas_dup = lojas.filter(database_name=db_name).order_by('created_at')
            
            for i, loja in enumerate(lojas_dup):
                self.stdout.write(f'   {i+1}. ID: {loja.id:3d} | {loja.nome:40s} | Criada: {loja.created_at}')
                lojas_problematicas.append(loja)
        
        return lojas_problematicas
    
    def _gerar_database_name_unico(self, loja):
        # Tentar usar o slug atual
        base = f"loja_{loja.slug.replace('-', '_')}"
        
        # Se já existe, adicionar sufixo
        if Loja.objects.filter(database_name=base).exclude(pk=loja.pk).exists():
            base = f"loja_{loja.slug.replace('-', '_')}_{loja.id}"
        
        # Validar formato
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', base):
            base = f"loja_id_{loja.id}"
        
        return base
    
    def _criar_schema_postgres(self, schema_name):
        try:
            with connection.cursor() as cursor:
                # Verificar se schema existe
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.schemata 
                    WHERE schema_name = %s
                """, [schema_name])
                
                exists = cursor.fetchone()[0] > 0
                
                if exists:
                    self.stdout.write(f'   ℹ️  Schema "{schema_name}" já existe')
                    return True
                
                # Criar schema
                cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
                self.stdout.write(self.style.SUCCESS(f'   ✅ Schema "{schema_name}" criado'))
                return True
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Erro ao criar schema "{schema_name}": {e}'))
            return False
    
    def _aplicar_migrations(self, loja):
        try:
            from django.core.management import call_command
            
            db_name = loja.database_name
            tipo_loja_nome = loja.tipo_loja.nome if loja.tipo_loja else ''
            
            self.stdout.write('   🔄 Aplicando migrations...')
            
            # Migrations básicas
            call_command('migrate', 'stores', '--database', db_name, verbosity=0)
            call_command('migrate', 'products', '--database', db_name, verbosity=0)
            
            # Migrations específicas
            if tipo_loja_nome == 'Clínica de Estética':
                call_command('migrate', 'clinica_estetica', '--database', db_name, verbosity=0)
            elif tipo_loja_nome == 'Restaurante':
                call_command('migrate', 'restaurante', '--database', db_name, verbosity=0)
            elif tipo_loja_nome == 'Serviços':
                call_command('migrate', 'servicos', '--database', db_name, verbosity=0)
            elif tipo_loja_nome == 'Cabeleireiro':
                call_command('migrate', 'cabeleireiro', '--database', db_name, verbosity=0)
            elif tipo_loja_nome == 'E-commerce':
                call_command('migrate', 'ecommerce', '--database', db_name, verbosity=0)
            
            self.stdout.write(self.style.SUCCESS('   ✅ Migrations aplicadas'))
            return True
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'   ⚠️  Erro ao aplicar migrations: {e}'))
            return False
    
    def _corrigir_loja(self, loja):
        self.stdout.write(f'\n📝 Corrigindo loja: {loja.nome} (ID: {loja.id})')
        self.stdout.write(f'   Database atual: {loja.database_name}')
        
        # Gerar novo database_name
        novo_db_name = self._gerar_database_name_unico(loja)
        self.stdout.write(f'   Novo database: {novo_db_name}')
        
        # Criar schema
        schema_name = novo_db_name.replace('-', '_')
        if not self._criar_schema_postgres(schema_name):
            self.stdout.write(self.style.ERROR('   ❌ Falha ao criar schema. Abortando correção desta loja.'))
            return False
        
        # Atualizar loja
        loja.database_name = novo_db_name
        loja.database_created = True
        loja.save(update_fields=['database_name', 'database_created'])
        self.stdout.write(self.style.SUCCESS('   ✅ Database_name atualizado'))
        
        # Aplicar migrations
        self._aplicar_migrations(loja)
        
        self.stdout.write(self.style.SUCCESS('   ✅ Loja corrigida com sucesso!'))
        return True
    
    def _corrigir_todas(self, lojas_problematicas, auto_confirm):
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('🔧 INICIANDO CORREÇÃO DE DATABASE_NAMES'))
        self.stdout.write(self.style.SUCCESS('='*80))
        
        self.stdout.write(self.style.WARNING(f'\n⚠️  Serão corrigidas {len(lojas_problematicas)} lojas'))
        self.stdout.write(self.style.WARNING('\n⚠️  ATENÇÃO:'))
        self.stdout.write('   - Cada loja receberá um novo database_name único')
        self.stdout.write('   - Um novo schema será criado no PostgreSQL')
        self.stdout.write('   - As lojas ficarão VAZIAS (sem dados)')
        self.stdout.write('   - Os dados antigos permanecerão no schema original')
        
        if not auto_confirm:
            confirmacao = input("\nDigite 'CONFIRMAR' para prosseguir: ")
            if confirmacao != 'CONFIRMAR':
                self.stdout.write(self.style.ERROR('❌ Operação cancelada.'))
                return
        
        # Agrupar por database_name
        grupos = defaultdict(list)
        for loja in lojas_problematicas:
            grupos[loja.database_name].append(loja)
        
        # Corrigir cada grupo
        sucesso = 0
        falhas = 0
        
        for db_name, lojas_grupo in grupos.items():
            self.stdout.write(f'\n{"="*80}')
            self.stdout.write(f'Corrigindo grupo: {db_name} ({len(lojas_grupo)} lojas)')
            self.stdout.write(f'{"="*80}')
            
            # Ordenar por data de criação (mais antiga primeiro)
            lojas_grupo.sort(key=lambda x: x.created_at)
            
            # Manter a primeira (mais antiga) com o database_name original
            for i, loja in enumerate(lojas_grupo):
                if i == 0:
                    self.stdout.write(self.style.SUCCESS(f'\n✅ Mantendo loja original: {loja.nome} (ID: {loja.id})'))
                    self.stdout.write(f'   Esta loja manterá o database_name: {db_name}')
                    self.stdout.write('   E manterá todos os dados existentes')
                    continue
                
                if self._corrigir_loja(loja):
                    sucesso += 1
                else:
                    falhas += 1
        
        # Resumo
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('📊 RESUMO DA CORREÇÃO'))
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(f'✅ Lojas corrigidas com sucesso: {sucesso}')
        self.stdout.write(f'❌ Lojas com falha: {falhas}')
        self.stdout.write(f'ℹ️  Lojas mantidas (originais): {len(grupos)}')
        self.stdout.write('='*80 + '\n')
        
        if falhas == 0:
            self.stdout.write(self.style.SUCCESS('✅ Todas as correções foram aplicadas com sucesso!'))
            self.stdout.write('\n📝 PRÓXIMOS PASSOS:')
            self.stdout.write('   1. Verificar que as lojas estão acessíveis')
            self.stdout.write('   2. As lojas corrigidas estarão VAZIAS')
            self.stdout.write('   3. Os clientes precisarão recadastrar seus dados')
            self.stdout.write('   4. Ou você pode migrar dados do schema antigo manualmente')
        else:
            self.stdout.write(self.style.WARNING('⚠️  Algumas correções falharam. Verifique os logs acima.'))
