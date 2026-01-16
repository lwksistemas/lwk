"""
Comando para criar banco de dados isolado para uma nova loja
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.management import call_command
import shutil
from pathlib import Path

class Command(BaseCommand):
    help = 'Cria um banco de dados isolado para uma nova loja'
    
    def add_arguments(self, parser):
        parser.add_argument('loja_slug', type=str, help='Slug da loja')
    
    def handle(self, *args, **options):
        loja_slug = options['loja_slug']
        db_name = f'loja_{loja_slug}'
        
        self.stdout.write(f'Criando banco isolado para loja: {loja_slug}')
        
        # Caminho do novo banco
        base_dir = settings.BASE_DIR
        new_db_path = base_dir / f'db_{db_name}.sqlite3'
        
        # Verificar se já existe
        if new_db_path.exists():
            self.stdout.write(self.style.WARNING(f'Banco {db_name} já existe!'))
            return
        
        # Adicionar banco às configurações dinamicamente
        settings.DATABASES[db_name] = {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': new_db_path,
        }
        
        # Criar banco e rodar migrations
        self.stdout.write('Executando migrations...')
        call_command('migrate', '--database', db_name, verbosity=0)
        
        self.stdout.write(self.style.SUCCESS(f'✅ Banco {db_name} criado com sucesso!'))
        self.stdout.write(f'Localização: {new_db_path}')
