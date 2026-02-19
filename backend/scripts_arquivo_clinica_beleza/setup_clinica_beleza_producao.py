"""
Script para configurar Clínica da Beleza em produção (Heroku) – cria tabelas manualmente via SQL.
Hoje o fluxo normal é via migrations. Use apenas se necessário.
Execute a partir da pasta backend: python scripts_arquivo_clinica_beleza/setup_clinica_beleza_producao.py
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

def criar_tabelas_clinica_beleza():
    print("🏥 Criando tabelas da Clínica da Beleza no Heroku...")
    
    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clinica_beleza_patient (
                id SERIAL PRIMARY KEY,
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
            );
        """)
        print("✅ Tabela clinica_beleza_patient criada")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clinica_beleza_professional (
                id SERIAL PRIMARY KEY,
                name VARCHAR(150) NOT NULL,
                specialty VARCHAR(150) NOT NULL,
                phone VARCHAR(20),
                email VARCHAR(254),
                active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
        """)
        print("✅ Tabela clinica_beleza_professional criada")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clinica_beleza_procedure (
                id SERIAL PRIMARY KEY,
                name VARCHAR(150) NOT NULL,
                description TEXT,
                price NUMERIC(10, 2) NOT NULL,
                duration INTEGER NOT NULL,
                active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
        """)
        print("✅ Tabela clinica_beleza_procedure criada")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clinica_beleza_appointment (
                id SERIAL PRIMARY KEY,
                date TIMESTAMP WITH TIME ZONE NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'SCHEDULED',
                patient_id INTEGER NOT NULL REFERENCES clinica_beleza_patient(id) ON DELETE CASCADE,
                professional_id INTEGER NOT NULL REFERENCES clinica_beleza_professional(id) ON DELETE CASCADE,
                procedure_id INTEGER NOT NULL REFERENCES clinica_beleza_procedure(id) ON DELETE CASCADE,
                notes TEXT,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
        """)
        print("✅ Tabela clinica_beleza_appointment criada")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clinica_beleza_payment (
                id SERIAL PRIMARY KEY,
                appointment_id INTEGER NOT NULL REFERENCES clinica_beleza_appointment(id) ON DELETE CASCADE,
                amount NUMERIC(10, 2) NOT NULL,
                payment_method VARCHAR(20) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                payment_date TIMESTAMP WITH TIME ZONE,
                notes TEXT,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
        """)
        print("✅ Tabela clinica_beleza_payment criada")
        
        cursor.execute("""
            INSERT INTO django_migrations (app, name, applied)
            VALUES ('clinica_beleza', '0001_initial', NOW())
            ON CONFLICT DO NOTHING;
        """)
        print("✅ Migração registrada")
    
    print("\n✨ Tabelas criadas com sucesso!")

if __name__ == '__main__':
    criar_tabelas_clinica_beleza()
