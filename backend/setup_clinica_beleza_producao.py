"""
Script para configurar Clínica da Beleza em produção (Heroku)
Cria as tabelas manualmente via SQL
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def criar_tabelas_clinica_beleza():
    print("🏥 Criando tabelas da Clínica da Beleza no Heroku...")
    
    with connection.cursor() as cursor:
        # Criar tabela Patient
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
        
        # Criar tabela Professional
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
        
        # Criar tabela Procedure
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
        
        # Criar tabela Appointment
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
        
        # Criar tabela Payment
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
        
        # Registrar migração
        cursor.execute("""
            INSERT INTO django_migrations (app, name, applied)
            VALUES ('clinica_beleza', '0001_initial', NOW())
            ON CONFLICT DO NOTHING;
        """)
        print("✅ Migração registrada")
    
    print("\n✨ Tabelas criadas com sucesso!")
    print("📝 Agora você pode executar: python criar_dados_clinica_beleza.py")

if __name__ == '__main__':
    criar_tabelas_clinica_beleza()
