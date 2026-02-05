#!/bin/bash
source venv/bin/activate
DJANGO_SETTINGS_MODULE=config.settings_local python manage.py shell << 'EOF'
import psycopg2
import os

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    
    # Verificar colunas da tabela cabeleireiro_clientes no schema loja_salao_000172
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'loja_salao_000172' 
        AND table_name = 'cabeleireiro_clientes'
        ORDER BY ordinal_position;
    """)
    
    print("Colunas da tabela loja_salao_000172.cabeleireiro_clientes:")
    for row in cur.fetchall():
        print(f"  - {row[0]}: {row[1]}")
    
    cur.close()
    conn.close()
EOF
