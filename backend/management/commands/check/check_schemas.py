"""
Management command para verificar schemas do banco de dados PostgreSQL
Migrado de: backend/check_schemas.py
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Verifica schemas do banco de dados PostgreSQL e seus dados'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar informações detalhadas de cada schema',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Limitar número de schemas a verificar (padrão: 20)',
        )
        parser.add_argument(
            '--check-leads',
            action='store_true',
            help='Verificar quantidade de leads em cada schema',
        )
    
    def handle(self, *args, **options):
        verbose = options['verbose']
        limit = options['limit']
        check_leads = options['check_leads']
        
        self.stdout.write(self.style.SUCCESS('🔍 Verificando schemas do banco de dados...'))
        self.stdout.write(f'Schema atual: {connection.schema_name}\n')
        
        # Listar todos os schemas
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name NOT IN ('public', 'information_schema', 'pg_catalog', 'pg_toast')
                ORDER BY schema_name
            """)
            schemas = [row[0] for row in cursor.fetchall()]
        
        if not schemas:
            self.stdout.write(self.style.WARNING('⚠️  Nenhum schema encontrado'))
            return
        
        self.stdout.write(f'📊 Total de schemas: {len(schemas)}')
        
        # Mostrar primeiros schemas
        schemas_to_show = schemas[:10]
        self.stdout.write(f'Primeiros schemas: {", ".join(schemas_to_show)}')
        
        if len(schemas) > 10:
            self.stdout.write(f'... e mais {len(schemas) - 10} schemas\n')
        
        # Verificar detalhes se verbose
        if verbose:
            self.stdout.write('\n' + '='*80)
            self.stdout.write('DETALHES DOS SCHEMAS')
            self.stdout.write('='*80 + '\n')
            
            for schema in schemas[:limit]:
                self._show_schema_details(schema)
        
        # Verificar leads se solicitado
        if check_leads:
            self._check_leads(schemas[:limit])
        
        self.stdout.write(self.style.SUCCESS('\n✅ Verificação concluída!'))
    
    def _show_schema_details(self, schema):
        """Mostra detalhes de um schema específico"""
        self.stdout.write(f'\n📁 Schema: {schema}')
        
        try:
            with connection.cursor() as cursor:
                # Contar tabelas
                cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = '{schema}'
                """)
                table_count = cursor.fetchone()[0]
                
                self.stdout.write(f'   Tabelas: {table_count}')
                
                # Listar algumas tabelas
                cursor.execute(f"""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = '{schema}'
                    ORDER BY table_name
                    LIMIT 5
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                if tables:
                    self.stdout.write(f'   Exemplos: {", ".join(tables)}')
                    if table_count > 5:
                        self.stdout.write(f'   ... e mais {table_count - 5} tabelas')
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Erro: {str(e)}'))
    
    def _check_leads(self, schemas):
        """Verifica quantidade de leads em cada schema"""
        self.stdout.write('\n' + '='*80)
        self.stdout.write('VERIFICANDO LEADS POR SCHEMA')
        self.stdout.write('='*80 + '\n')
        
        try:
            from crm_vendas.models import Lead
            
            for schema in schemas:
                try:
                    # Usar schema_context se disponível
                    try:
                        from django_tenants.utils import schema_context
                        with schema_context(schema):
                            count = Lead.objects.count()
                            if count > 0:
                                self.stdout.write(
                                    self.style.SUCCESS(f'✅ Schema "{schema}": {count} leads')
                                )
                    except ImportError:
                        # Fallback: usar SET search_path
                        with connection.cursor() as cursor:
                            cursor.execute(f"SET search_path TO {schema}")
                            count = Lead.objects.count()
                            if count > 0:
                                self.stdout.write(
                                    self.style.SUCCESS(f'✅ Schema "{schema}": {count} leads')
                                )
                            cursor.execute("SET search_path TO public")
                
                except Exception as e:
                    # Silenciar erros de schemas sem tabela de leads
                    pass
        
        except ImportError:
            self.stdout.write(
                self.style.WARNING('⚠️  Modelo Lead não disponível (app crm_vendas não instalado)')
            )
