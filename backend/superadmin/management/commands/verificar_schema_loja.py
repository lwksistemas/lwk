"""
Comando para verificar e corrigir schema de uma loja antes de importar backup
"""
from django.core.management.base import BaseCommand
from django.db import connections
from superadmin.models import Loja
from superadmin.services.database_schema_service import DatabaseSchemaService


class Command(BaseCommand):
    help = 'Verifica e corrige schema de uma loja para importação de backup'

    def add_arguments(self, parser):
        parser.add_argument('loja_id', type=int, help='ID da loja')
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Aplicar migrations se necessário'
        )

    def handle(self, *args, **options):
        loja_id = options['loja_id']
        fix = options['fix']
        
        try:
            loja = Loja.objects.get(id=loja_id)
        except Loja.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Loja com ID {loja_id} não encontrada'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'\n{"="*60}'))
        self.stdout.write(self.style.SUCCESS(f'Loja: {loja.nome} (ID: {loja.id})'))
        self.stdout.write(self.style.SUCCESS(f'Slug: {loja.slug}'))
        self.stdout.write(self.style.SUCCESS(f'Database: {loja.database_name}'))
        self.stdout.write(self.style.SUCCESS(f'{"="*60}\n'))
        
        # Verificar se banco está configurado
        if loja.database_name not in connections.databases:
            self.stdout.write(self.style.WARNING('⚠️ Banco não configurado. Adicionando...'))
            if DatabaseSchemaService.adicionar_configuracao_django(loja):
                self.stdout.write(self.style.SUCCESS('✅ Configuração adicionada'))
            else:
                self.stdout.write(self.style.ERROR('❌ Falha ao adicionar configuração'))
                return
        
        # Verificar tabelas
        schema_name = loja.database_name.replace('-', '_')
        connection = connections[loja.database_name]
        
        try:
            with connection.cursor() as cursor:
                # Verificar se schema existe
                cursor.execute(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                    [schema_name]
                )
                schema_exists = cursor.fetchone() is not None
                
                if not schema_exists:
                    self.stdout.write(self.style.WARNING(f'⚠️ Schema "{schema_name}" não existe'))
                    if fix:
                        self.stdout.write('Criando schema...')
                        cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
                        self.stdout.write(self.style.SUCCESS('✅ Schema criado'))
                    else:
                        self.stdout.write(self.style.WARNING('Use --fix para criar o schema'))
                        return
                
                # Listar tabelas
                cursor.execute(
                    """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = %s 
                    ORDER BY table_name
                    """,
                    [schema_name]
                )
                tabelas = [row[0] for row in cursor.fetchall()]
                
                self.stdout.write(f'\n=== Tabelas no schema ({len(tabelas)}) ===')
                if tabelas:
                    for t in tabelas[:10]:  # Mostrar apenas primeiras 10
                        self.stdout.write(f'  - {t}')
                    if len(tabelas) > 10:
                        self.stdout.write(f'  ... e mais {len(tabelas) - 10} tabelas')
                else:
                    self.stdout.write(self.style.WARNING('  Nenhuma tabela encontrada'))
                
                # Verificar tabelas CRM
                tabelas_crm = [
                    'crm_vendas_vendedor',
                    'crm_vendas_conta',
                    'crm_vendas_lead',
                    'crm_vendas_oportunidade',
                    'crm_vendas_atividade',
                    'crm_vendas_contato',
                    'crm_vendas_config',
                ]
                
                self.stdout.write(f'\n=== Tabelas CRM Vendas ===')
                faltando = []
                for t in tabelas_crm:
                    existe = t in tabelas
                    if existe:
                        self.stdout.write(self.style.SUCCESS(f'✅ {t}'))
                    else:
                        self.stdout.write(self.style.ERROR(f'❌ {t}'))
                        faltando.append(t)
                
                # Se faltam tabelas e --fix foi passado, aplicar migrations
                if faltando:
                    self.stdout.write(self.style.WARNING(f'\n⚠️ Faltam {len(faltando)} tabelas do CRM'))
                    
                    if fix:
                        self.stdout.write('\nAplicando migrations...')
                        if DatabaseSchemaService.aplicar_migrations(loja):
                            self.stdout.write(self.style.SUCCESS('✅ Migrations aplicadas'))
                            
                            # Verificar novamente
                            cursor.execute(
                                """
                                SELECT table_name 
                                FROM information_schema.tables 
                                WHERE table_schema = %s 
                                ORDER BY table_name
                                """,
                                [schema_name]
                            )
                            tabelas = [row[0] for row in cursor.fetchall()]
                            
                            self.stdout.write(f'\n=== Verificação pós-migrations ===')
                            todas_ok = True
                            for t in tabelas_crm:
                                existe = t in tabelas
                                if existe:
                                    self.stdout.write(self.style.SUCCESS(f'✅ {t}'))
                                else:
                                    self.stdout.write(self.style.ERROR(f'❌ {t}'))
                                    todas_ok = False
                            
                            if todas_ok:
                                self.stdout.write(self.style.SUCCESS(f'\n{"="*60}'))
                                self.stdout.write(self.style.SUCCESS('✅ SCHEMA OK - Pronto para importar backup!'))
                                self.stdout.write(self.style.SUCCESS(f'{"="*60}\n'))
                            else:
                                self.stdout.write(self.style.ERROR(f'\n{"="*60}'))
                                self.stdout.write(self.style.ERROR('❌ Ainda faltam tabelas após migrations'))
                                self.stdout.write(self.style.ERROR(f'{"="*60}\n'))
                        else:
                            self.stdout.write(self.style.ERROR('❌ Falha ao aplicar migrations'))
                    else:
                        self.stdout.write(self.style.WARNING('\nUse --fix para aplicar migrations'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'\n{"="*60}'))
                    self.stdout.write(self.style.SUCCESS('✅ SCHEMA OK - Pronto para importar backup!'))
                    self.stdout.write(self.style.SUCCESS(f'{"="*60}\n'))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro: {e}'))
            import traceback
            traceback.print_exc()
