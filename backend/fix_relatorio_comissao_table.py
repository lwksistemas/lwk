"""
Remove tabela legado crm_relatorio_comissao do schema da loja FELIX REPRESENTAÇÕES.
Executado no release do Procfile.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lwk_project.settings')
django.setup()

from django.db import connection

print("🧹 Verificando tabela legado crm_relatorio_comissao...")

# Schema conhecido da loja FELIX REPRESENTAÇÕES (CRM Vendas)
schema = 'loja_41449198000172'

try:
    with connection.cursor() as cur:
        cur.execute(f'SET search_path TO "{schema}", public')
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = %s AND table_name = 'crm_relatorio_comissao'
            )
        """, [schema])
        exists = cur.fetchone()[0]
        if exists:
            cur.execute('DROP TABLE IF EXISTS crm_relatorio_comissao CASCADE')
            print(f"  ✅ Tabela crm_relatorio_comissao removida de {schema}")
        else:
            print(f"  ✅ {schema}: tabela já não existe — OK")
except Exception as e:
    print(f"  ⚠️ Erro: {e}")

print("Done.")
