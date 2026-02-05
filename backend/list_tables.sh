#!/bin/bash
source venv/bin/activate
DJANGO_SETTINGS_MODULE=config.settings_local python manage.py shell << 'EOF'
import psycopg2
import os

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    
    # Listar todas as tabelas no schema loja_salao_000172
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'loja_salao_000172'
        ORDER BY table_name;
    """)
    
    print("Tabelas no schema loja_salao_000172:")
    for row in cur.fetchall():
        print(f"  - {row[0]}")
    
    cur.close()
    conn.close()
EOF
