"""
Comando para aplicar migrations em todas as lojas ativas.

Uso:
    python manage.py migrate_all_lojas [app_label]
    python manage.py migrate_all_lojas ecommerce
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from superadmin.models import Loja
from core.db_config import ensure_loja_database_config


class Command(BaseCommand):
    help = 'Aplica migrations em todas as lojas ativas'

    def add_arguments(self, parser):
        parser.add_argument(
            'app_label',
            nargs='?',
            help='App específico para migrar (opcional)',
        )
        parser.add_argument(
            '--fake',
            action='store_true',
            help='Marca migrations como aplicadas sem executar',
        )

    def handle(self, *args, **options):
        app_label = options.get('app_label')
        fake = options.get('fake', False)
        
        # Buscar todas as lojas ativas
        lojas = Loja.objects.filter(is_active=True, database_created=True)
        
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(f"APLICANDO MIGRATIONS EM {lojas.count()} LOJAS")
        self.stdout.write(f"{'='*80}\n")
        
        sucesso = 0
        erros = 0
        
        for loja in lojas:
            try:
                self.stdout.write(f"\n📦 Loja: {loja.nome} ({loja.database_name})")
                
                # Garantir que database está configurado
                if not ensure_loja_database_config(loja.database_name):
                    self.stdout.write(
                        self.style.ERROR(f"  ❌ Erro ao configurar database")
                    )
                    erros += 1
                    continue
                
                # Aplicar migrations
                migrate_args = [app_label] if app_label else []
                migrate_kwargs = {
                    'database': loja.database_name,
                    'verbosity': 1,
                    'interactive': False,
                }
                
                if fake:
                    migrate_kwargs['fake'] = True
                
                call_command('migrate', *migrate_args, **migrate_kwargs)
                
                self.stdout.write(
                    self.style.SUCCESS(f"  ✅ Migrations aplicadas com sucesso")
                )
                sucesso += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ❌ Erro: {str(e)}")
                )
                erros += 1
        
        # Resumo
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write("RESUMO")
        self.stdout.write(f"{'='*80}")
        self.stdout.write(f"✅ Sucesso: {sucesso}")
        self.stdout.write(f"❌ Erros: {erros}")
        self.stdout.write(f"📊 Total: {lojas.count()}\n")
