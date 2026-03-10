from superadmin.models import Loja
from django.conf import settings
import dj_database_url
import os

# Configurar loja
loja = Loja.objects.get(id=200)
print(f"Loja: {loja.nome}")
print(f"Slug: {loja.slug}")
print(f"Database: {loja.database_name}")

# Configurar banco
DATABASE_URL = os.environ.get('DATABASE_URL')
schema_name = loja.database_name.replace('-', '_')
default_db = dj_database_url.config(default=DATABASE_URL, conn_max_age=0)
settings.DATABASES[loja.database_name] = {
    **default_db,
    'OPTIONS': {'options': f'-c search_path={schema_name},public'},
    'TIME_ZONE': None,
}

# Verificar dados
from django.db import connections
conn = connections[loja.database_name]

with conn.cursor() as cursor:
    cursor.execute("SELECT COUNT(*) FROM crm_vendas_lead")
    leads = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM crm_vendas_atividade")
    atividades = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM crm_vendas_vendedor")
    vendedores = cursor.fetchone()[0]

print(f"Vendedores: {vendedores}")
print(f"Leads: {leads}")
print(f"Atividades: {atividades}")

# Criar dados de teste se não existirem
if leads == 0:
    print("Criando lead de teste...")
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO crm_vendas_lead 
            (nome, empresa, email, telefone, origem, status, loja_id, created_at, updated_at)
            VALUES 
            ('Lead Teste', 'Empresa Teste', 'teste@teste.com', '11999999999', 'site', 'novo', %s, NOW(), NOW())
            RETURNING id
        """, [loja.id])
        lead_id = cursor.fetchone()[0]
        print(f"Lead criado: {lead_id}")

if atividades == 0:
    print("Criando atividade de teste...")
    with conn.cursor() as cursor:
        cursor.execute("SELECT id FROM crm_vendas_lead LIMIT 1")
        result = cursor.fetchone()
        if result:
            lead_id = result[0]
            cursor.execute("""
                INSERT INTO crm_vendas_atividade 
                (titulo, tipo, data, duracao_minutos, concluido, loja_id, lead_id, created_at, updated_at)
                VALUES 
                ('Reunião Teste', 'meeting', NOW() + INTERVAL '1 day', 60, false, %s, %s, NOW(), NOW())
                RETURNING id
            """, [loja.id, lead_id])
            atividade_id = cursor.fetchone()[0]
            print(f"Atividade criada: {atividade_id}")

print("Concluido!")
