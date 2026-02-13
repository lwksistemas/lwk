"""
Script para criar tabelas da Clínica da Beleza manualmente em um schema
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

def create_tables(loja_id):
    """Cria tabelas da Clínica da Beleza em um schema específico"""
    try:
        loja = Loja.objects.get(id=loja_id)
        schema_name = loja.database_name
        
        print(f"🔧 Criando tabelas no schema: {schema_name} (loja_id={loja_id})")
        
        with connection.cursor() as cursor:
            # Setar o schema
            cursor.execute(f"SET search_path TO {schema_name}")
            
            # Criar tabela Patient
            print("📦 Criando tabela clinica_beleza_patient...")
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {schema_name}.clinica_beleza_patient (
                    id SERIAL PRIMARY KEY,
                    loja_id INTEGER NOT NULL DEFAULT {loja_id},
                    name VARCHAR(150) NOT NULL,
                    phone VARCHAR(20) NOT NULL,
                    email VARCHAR(254),
                    cpf VARCHAR(14),
                    birth_date DATE,
                    address TEXT,
                    notes TEXT,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    active BOOLEAN NOT NULL DEFAULT TRUE
                )
            """)
            cursor.execute(f"CREATE INDEX IF NOT EXISTS clinica_beleza_patient_loja_id_idx ON {schema_name}.clinica_beleza_patient (loja_id)")
            
            # Criar tabela Professional
            print("📦 Criando tabela clinica_beleza_professional...")
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {schema_name}.clinica_beleza_professional (
                    id SERIAL PRIMARY KEY,
                    loja_id INTEGER NOT NULL DEFAULT {loja_id},
                    name VARCHAR(150) NOT NULL,
                    specialty VARCHAR(150) NOT NULL,
                    phone VARCHAR(20),
                    email VARCHAR(254),
                    active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                )
            """)
            cursor.execute(f"CREATE INDEX IF NOT EXISTS clinica_beleza_professional_loja_id_idx ON {schema_name}.clinica_beleza_professional (loja_id)")
            
            # Criar tabela Procedure
            print("📦 Criando tabela clinica_beleza_procedure...")
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {schema_name}.clinica_beleza_procedure (
                    id SERIAL PRIMARY KEY,
                    loja_id INTEGER NOT NULL DEFAULT {loja_id},
                    name VARCHAR(150) NOT NULL,
                    description TEXT,
                    price NUMERIC(10, 2) NOT NULL,
                    duration INTEGER NOT NULL,
                    active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                )
            """)
            cursor.execute(f"CREATE INDEX IF NOT EXISTS clinica_beleza_procedure_loja_id_idx ON {schema_name}.clinica_beleza_procedure (loja_id)")
            
            # Criar tabela Appointment
            print("📦 Criando tabela clinica_beleza_appointment...")
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {schema_name}.clinica_beleza_appointment (
                    id SERIAL PRIMARY KEY,
                    loja_id INTEGER NOT NULL DEFAULT {loja_id},
                    date TIMESTAMP WITH TIME ZONE NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'SCHEDULED',
                    patient_id INTEGER NOT NULL REFERENCES {schema_name}.clinica_beleza_patient(id) ON DELETE CASCADE,
                    professional_id INTEGER NOT NULL REFERENCES {schema_name}.clinica_beleza_professional(id) ON DELETE CASCADE,
                    procedure_id INTEGER NOT NULL REFERENCES {schema_name}.clinica_beleza_procedure(id) ON DELETE CASCADE,
                    notes TEXT,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                )
            """)
            cursor.execute(f"CREATE INDEX IF NOT EXISTS clinica_beleza_appointment_loja_id_idx ON {schema_name}.clinica_beleza_appointment (loja_id)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS clinica_beleza_appointment_date_idx ON {schema_name}.clinica_beleza_appointment (date)")
            
            # Criar tabela BloqueioHorario
            print("📦 Criando tabela clinica_beleza_bloqueiohorario...")
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {schema_name}.clinica_beleza_bloqueiohorario (
                    id SERIAL PRIMARY KEY,
                    loja_id INTEGER NOT NULL DEFAULT {loja_id},
                    professional_id INTEGER REFERENCES {schema_name}.clinica_beleza_professional(id) ON DELETE CASCADE,
                    data_inicio TIMESTAMP WITH TIME ZONE NOT NULL,
                    data_fim TIMESTAMP WITH TIME ZONE NOT NULL,
                    motivo VARCHAR(100) NOT NULL,
                    observacoes TEXT,
                    criado_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                )
            """)
            cursor.execute(f"CREATE INDEX IF NOT EXISTS clinica_beleza_bloqueiohorario_loja_id_idx ON {schema_name}.clinica_beleza_bloqueiohorario (loja_id)")
            
            # Criar tabela Payment
            print("📦 Criando tabela clinica_beleza_payment...")
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {schema_name}.clinica_beleza_payment (
                    id SERIAL PRIMARY KEY,
                    loja_id INTEGER NOT NULL DEFAULT {loja_id},
                    appointment_id INTEGER NOT NULL REFERENCES {schema_name}.clinica_beleza_appointment(id) ON DELETE CASCADE,
                    amount NUMERIC(10, 2) NOT NULL,
                    payment_method VARCHAR(20) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                    payment_date TIMESTAMP WITH TIME ZONE,
                    notes TEXT,
                    comissao_percentual SMALLINT NOT NULL DEFAULT 0,
                    comissao_valor NUMERIC(10, 2) NOT NULL DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                )
            """)
            cursor.execute(f"CREATE INDEX IF NOT EXISTS clinica_beleza_payment_loja_id_idx ON {schema_name}.clinica_beleza_payment (loja_id)")
            
            print(f"✅ Tabelas criadas com sucesso no schema {schema_name}!")
            
    except Loja.DoesNotExist:
        print(f"❌ Loja {loja_id} não encontrada")
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python create_clinica_beleza_tables.py <loja_id>")
        print("\nLojas disponíveis:")
        for loja in Loja.objects.filter(is_active=True):
            print(f"  - ID: {loja.id}, Slug: {loja.slug}, Tipo: {loja.tipo_loja.slug}, Schema: {loja.database_name}")
        sys.exit(1)
    
    loja_id = int(sys.argv[1])
    create_tables(loja_id)
