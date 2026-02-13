"""
Script para aplicar migrations da Clínica da Beleza em um schema específico
"""
import os
import django
import sys

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command
from django.db import connection
from superadmin.models import Loja

def apply_migrations(loja_id):
    """Aplica migrations da Clínica da Beleza em um schema específico"""
    try:
        loja = Loja.objects.get(id=loja_id)
        schema_name = loja.database_name
        
        print(f"🔧 Aplicando migrations no schema: {schema_name} (loja_id={loja_id})")
        
        # Setar o schema
        with connection.cursor() as cursor:
            cursor.execute(f"SET search_path TO {schema_name}")
            print(f"✅ Schema setado: {schema_name}")
        
        # Aplicar migrations do clinica_beleza
        print("📦 Aplicando migrations do clinica_beleza...")
        call_command('migrate', 'clinica_beleza', '--database=default', verbosity=2)
        
        print(f"✅ Migrations aplicadas com sucesso no schema {schema_name}!")
        
    except Loja.DoesNotExist:
        print(f"❌ Loja {loja_id} não encontrada")
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python apply_clinica_beleza_migrations.py <loja_id>")
        print("\nLojas disponíveis:")
        for loja in Loja.objects.filter(tipo_loja__slug='clinica_beleza', is_active=True):
            print(f"  - ID: {loja.id}, Slug: {loja.slug}, Schema: {loja.database_name}")
        sys.exit(1)
    
    loja_id = int(sys.argv[1])
    apply_migrations(loja_id)
