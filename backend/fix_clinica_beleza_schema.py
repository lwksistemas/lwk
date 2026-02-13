"""
Script para adicionar coluna loja_id nas tabelas da Clínica da Beleza
"""
import os
import django
import sys

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from superadmin.models import Loja

def fix_clinica_beleza_schema(loja_id):
    """Adiciona coluna loja_id nas tabelas da Clínica da Beleza"""
    try:
        loja = Loja.objects.get(id=loja_id)
        schema_name = loja.schema_name
        
        print(f"🔧 Corrigindo schema: {schema_name} (loja_id={loja_id})")
        
        with connection.cursor() as cursor:
            # Setar o schema
            cursor.execute(f"SET search_path TO {schema_name}")
            
            # Lista de tabelas para adicionar loja_id
            tables = [
                'clinica_beleza_patient',
                'clinica_beleza_professional',
                'clinica_beleza_procedure',
                'clinica_beleza_appointment',
                'clinica_beleza_bloqueiohorario',
                'clinica_beleza_payment',
            ]
            
            for table in tables:
                # Verificar se a coluna já existe
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
                
                # Adicionar coluna loja_id
                print(f"  ➕ {table}: adicionando loja_id...")
                cursor.execute(f"""
                    ALTER TABLE {schema_name}.{table} 
                    ADD COLUMN loja_id INTEGER NOT NULL DEFAULT {loja_id}
                """)
                
                # Criar índice
                print(f"  📊 {table}: criando índice...")
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
        print("Uso: python fix_clinica_beleza_schema.py <loja_id>")
        print("\nLojas disponíveis:")
        for loja in Loja.objects.filter(tipo_loja='clinica_beleza', is_active=True):
            print(f"  - ID: {loja.id}, Slug: {loja.slug}, Schema: {loja.schema_name}")
        sys.exit(1)
    
    loja_id = int(sys.argv[1])
    fix_clinica_beleza_schema(loja_id)
