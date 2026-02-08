"""
Comando para criar tabelas nos schemas das lojas existentes
Usa SQL direto para copiar estrutura do schema public
"""
from django.core.management.base import BaseCommand
from django.db import connection
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Cria tabelas (aplica migrations) nos schemas das lojas existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loja-id',
            type=int,
            help='ID da loja específica (opcional)',
        )

    def handle(self, *args, **options):
        loja_id = options.get('loja_id')

        self.stdout.write('\n' + '='*100)
        self.stdout.write('🔧 CRIAÇÃO DE TABELAS NOS SCHEMAS DAS LOJAS')
        self.stdout.write('='*100 + '\n')

        # Buscar lojas
        if loja_id:
            lojas = Loja.objects.filter(id=loja_id, is_active=True)
        else:
            lojas = Loja.objects.filter(
                is_active=True,
                tipo_loja__nome='Clínica de Estética'
            ).order_by('created_at')

        if not lojas.exists():
            self.stdout.write(self.style.ERROR('❌ Nenhuma loja encontrada'))
            return

        self.stdout.write(f'📊 Total de lojas: {lojas.count()}\n')

        for loja in lojas:
            self.stdout.write('-' * 100)
            self.stdout.write(f'\n🏪 Loja: {loja.nome} (ID: {loja.id})')
            self.stdout.write(f'   Database: {loja.database_name}')
            self.stdout.write(f'   Tipo: {loja.tipo_loja.nome if loja.tipo_loja else "N/A"}')

            schema_name = loja.database_name.replace('-', '_')
            self.stdout.write(f'   Schema: {schema_name}')

            try:
                with connection.cursor() as cursor:
                    # Verificar se schema existe
                    cursor.execute("""
                        SELECT schema_name 
                        FROM information_schema.schemata 
                        WHERE schema_name = %s
                    """, [schema_name])
                    
                    if not cursor.fetchone():
                        self.stdout.write(self.style.ERROR(f'\n   ❌ Schema {schema_name} não existe'))
                        continue

                    self.stdout.write(f'\n   🔄 Criando tabelas no schema {schema_name}...')

                    # Listar tabelas que precisam ser criadas
                    tabelas_clinica = [
                        'clinica_clientes',
                        'clinica_profissionais',
                        'clinica_procedimentos',
                        'clinica_agendamentos',
                        'clinica_funcionarios',
                        'clinica_protocolos',
                        'clinica_consultas',
                        'clinica_evolucoes',
                        'clinica_anamneses_templates',
                        'clinica_anamneses',
                        'clinica_horarios_funcionamento',
                        'clinica_bloqueios_agenda',
                        'clinica_historico_login',
                        'clinica_categorias_financeiras',
                        'clinica_transacoes'
                    ]

                    tabelas_criadas = 0
                    
                    for tabela in tabelas_clinica:
                        # Verificar se tabela já existe no schema
                        cursor.execute("""
                            SELECT table_name 
                            FROM information_schema.tables 
                            WHERE table_schema = %s AND table_name = %s
                        """, [schema_name, tabela])
                        
                        if cursor.fetchone():
                            self.stdout.write(f'      ⏭️  {tabela} (já existe)')
                            continue

                        # Copiar estrutura da tabela do schema public
                        try:
                            cursor.execute(f"""
                                CREATE TABLE {schema_name}.{tabela} 
                                (LIKE public.{tabela} INCLUDING ALL)
                            """)
                            self.stdout.write(f'      ✅ {tabela}')
                            tabelas_criadas += 1
                        except Exception as e:
                            self.stdout.write(f'      ⚠️  {tabela}: {str(e)[:50]}')

                    if tabelas_criadas > 0:
                        self.stdout.write(self.style.SUCCESS(f'\n   ✅ {tabelas_criadas} tabelas criadas com sucesso!'))
                    else:
                        self.stdout.write(self.style.WARNING(f'\n   ⚠️  Nenhuma tabela nova criada (todas já existiam)'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'\n   ❌ Erro: {e}'))

        self.stdout.write('\n' + '='*100)
        self.stdout.write(self.style.SUCCESS('✅ Processo concluído!'))
        self.stdout.write('='*100 + '\n')
