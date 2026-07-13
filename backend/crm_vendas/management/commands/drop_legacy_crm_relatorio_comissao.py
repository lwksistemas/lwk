"""Remove tabela legado crm_relatorio_comissao do schema CRM Vendas.
Uso: python manage.py drop_legacy_crm_relatorio_comissao
"""
from django.core.management.base import BaseCommand
from django.db import connection

from superadmin.models import Loja


class Command(BaseCommand):
    help = "Remove tabela legado crm_relatorio_comissao dos schemas CRM Vendas"

    def handle(self, *args, **options):
        lojas = Loja.objects.filter(is_active=True, tipo_loja__nome__icontains="CRM")
        if not lojas.exists():
            lojas = Loja.objects.filter(cpf_cnpj="41.449.198/0001-72")

        for loja in lojas:
            cpf = loja.cpf_cnpj.replace(".", "").replace("-", "").replace("/", "")
            schema = f"loja_{cpf}"
            self.stdout.write(f"Verificando {loja.nome} ({schema})...")

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

                    if not exists:
                        self.stdout.write(self.style.SUCCESS("  ✅ Tabela não existe — OK"))
                        continue

                    cur.execute("SELECT COUNT(*) FROM crm_relatorio_comissao")
                    count = cur.fetchone()[0]
                    self.stdout.write(f"  Registros: {count}")

                    cur.execute("DROP TABLE IF EXISTS crm_relatorio_comissao CASCADE")
                    self.stdout.write(self.style.SUCCESS("  ✅ Tabela crm_relatorio_comissao removida"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ❌ Erro: {e}"))

        self.stdout.write(self.style.SUCCESS("\nDone!"))
