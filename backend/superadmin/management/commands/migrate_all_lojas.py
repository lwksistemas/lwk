"""
Comando para aplicar migrations em todos os schemas das lojas
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from superadmin.models import Loja
import dj_database_url
import os


class Command(BaseCommand):
    help = 'Aplica migrations em todos os schemas das lojas'

    def handle(self, *args, **options):
        self.stdout.write("🔧 Aplicando migrations em todas as lojas...\n")
        
        lojas = Loja.objects.all()
        self.stdout.write(f"📊 Total de lojas: {lojas.count()}\n")
        
        # Configurar bancos das lojas
        DATABASE_URL = os.environ.get('DATABASE_URL')
        if not DATABASE_URL:
            self.stdout.write(self.style.ERROR("❌ DATABASE_URL não configurada"))
            return
        
        for loja in lojas:
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"Loja: {loja.nome} (ID: {loja.id})")
            self.stdout.write(f"Database: {loja.database_name}")
            # Schema no PostgreSQL = database_name (ex: loja_teste_5889), alinhado ao TenantMiddleware
            schema_name = loja.database_name.replace('-', '_')
            
            # Adicionar banco às configurações se não existir
            if loja.database_name not in settings.DATABASES:
                default_db = dj_database_url.config(default=DATABASE_URL, conn_max_age=600)
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
                self.stdout.write(f"✅ Banco configurado")
            
            # Aplicar migrations
            tipo_slug = loja.tipo_loja.slug if loja.tipo_loja else 'unknown'
            
            # Apps base (sempre aplicar)
            base_apps = ['stores', 'products']
            
            # Apps específicos por tipo de loja
            tipo_apps = {
                'clinica-de-estetica': ['clinica_estetica'],
                'clinica-da-beleza': ['clinica_beleza'],
                'crm-vendas': ['crm_vendas'],
                'e-commerce': ['ecommerce'],
                'restaurante': ['restaurante'],
                'servicos': ['servicos'],
                'cabeleireiro': ['cabeleireiro'],
            }
            
            apps_to_migrate = base_apps + tipo_apps.get(tipo_slug, [])
            
            for app in apps_to_migrate:
                try:
                    self.stdout.write(f"  Migrando {app}...")
                    call_command(
                        'migrate', 
                        app, 
                        '--database', loja.database_name,
                        verbosity=0
                    )
                    self.stdout.write(self.style.SUCCESS(f"  ✅ {app} migrado"))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"  ⚠️ Erro em {app}: {e}"))
        
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(self.style.SUCCESS("\n✅ Processo concluído!"))
