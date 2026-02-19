"""
Script para adicionar coluna loja_id nas tabelas da Clínica da Beleza (one-off).
Uso: cd backend && python scripts_arquivo_clinica_beleza/fix_clinica_beleza_schema.py <loja_id>
"""
import os
import sys

_script_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_script_dir)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.db import connection
from superadmin.models import Loja

def fix_clinica_beleza_schema(loja_id):
    """Adiciona coluna loja_id nas tabelas da Clínica da Beleza"""
    try:
        loja = Loja.objects.get(id=loja_id)
        schema_name = loja.database_name
        
        print(f"🔧 Corrigindo schema: {schema_name} (loja_id={loja_id})")
        
        with connection.cursor() as cursor:
            cursor.execute(f"SET search_path TO {schema_name}")
            
            tables = [
                'clinica_beleza_patient',
                'clinica_beleza_professional',
                'clinica_beleza_procedure',
                'clinica_beleza_appointment',
                'clinica_beleza_bloqueiohorario',
                'clinica_beleza_payment',
            ]
            
            for table in tables:
                cursor.execute(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = '{schema_name}' 
                    AND table_name = '{table}' 
                    AND column_name = 'loja_id'
                """)
                
                if cursor.fetchone():
                    print(f"  ✅ {table}: loja_id já existe")
                    continue
                
                print(f"  ➕ {table}: adicionando loja_id...")
                cursor.execute(f"""
                    ALTER TABLE {schema_name}.{table} 
                    ADD COLUMN loja_id INTEGER NOT NULL DEFAULT {loja_id}
                """)
                
                index_name = f"{table}_loja_id_idx"
                cursor.execute(f"""
                    CREATE INDEX IF NOT EXISTS {index_name} 
                    ON {schema_name}.{table} (loja_id)
                """)
                print(f"  ✅ {table}: concluído")
            
            print(f"✅ Schema {schema_name} corrigido com sucesso!")
            
    except Loja.DoesNotExist:
        print(f"❌ Loja {loja_id} não encontrada")
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python scripts_arquivo_clinica_beleza/fix_clinica_beleza_schema.py <loja_id>")
        print("\nLojas disponíveis:")
        for loja in Loja.objects.filter(tipo_loja__slug='clinica-da-beleza'):
            print(f"  - ID: {loja.id}, Slug: {loja.slug}, Schema: {loja.database_name}")
        sys.exit(1)
    
    loja_id = int(sys.argv[1])
    fix_clinica_beleza_schema(loja_id)
