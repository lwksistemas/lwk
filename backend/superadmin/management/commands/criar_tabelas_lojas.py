"""
Comando para criar tabelas nos schemas das lojas existentes
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from superadmin.models import Loja
import dj_database_url
import os


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

            # Adicionar configuração do banco se não existir
            DATABASE_URL = os.environ.get('DATABASE_URL')
            if DATABASE_URL and loja.database_name not in settings.DATABASES:
                default_db = dj_database_url.config(default=DATABASE_URL, conn_max_age=600)
                schema_name = loja.database_name.replace('-', '_')
                settings.DATABASES[loja.database_name] = {
                    **default_db,
                    'OPTIONS': {
                        'options': f'-c search_path={schema_name},public'
                    },
                    'ATOMIC_REQUESTS': False,
                    'AUTOCOMMIT': True,
                    'CONN_MAX_AGE': 600,
                    'CONN_HEALTH_CHECKS': True,
                    'TIME_ZONE': None,
                }
                self.stdout.write(f'   ✓ Configuração de banco adicionada')

            # Aplicar migrations
            try:
                self.stdout.write(f'\n   🔄 Aplicando migrations...')
                
                # Migrations básicas
                call_command('migrate', 'stores', '--database', loja.database_name, verbosity=0)
                self.stdout.write(f'   ✓ stores')
                
                call_command('migrate', 'products', '--database', loja.database_name, verbosity=0)
                self.stdout.write(f'   ✓ products')
                
                # Migrations específicas por tipo
                if loja.tipo_loja.nome == 'Clínica de Estética':
                    call_command('migrate', 'clinica_estetica', '--database', loja.database_name, verbosity=0)
                    self.stdout.write(f'   ✓ clinica_estetica')
                
                self.stdout.write(self.style.SUCCESS(f'\n   ✅ Migrations aplicadas com sucesso!'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'\n   ❌ Erro ao aplicar migrations: {e}'))

        self.stdout.write('\n' + '='*100)
        self.stdout.write(self.style.SUCCESS('✅ Processo concluído!'))
        self.stdout.write('='*100 + '\n')
