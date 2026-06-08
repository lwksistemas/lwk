"""
Remove tabela legado crm_relatorio_comissao do schema da loja FELIX REPRESENTAÇÕES.
Executado no release do Procfile.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lwk_project.settings')
django.setup()

from django.db import connection
from superadmin.models import Loja

print("🧹 Verificando tabela legado crm_relatorio_comissao...")

# Buscar lojas CRM
try:
    lojas = list(Loja.objects.filter(cpf_cnpj='41.449.198/0001-72')) or list(
        Loja.objects.filter(tipo_loja__nome__icontains='CRM')
    )
except Exception:
    lojas = []

for loja in lojas:
    cpf = loja.cpf_cnpj.replace('.', '').replace('-', '').replace('/', '')
    schema = f'loja_{cpf}'
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
                print(f"  ✅ {schema}: tabela já não existe")
    except Exception as e:
        print(f"  ⚠️ {schema}: {e}")

print("Done.")
