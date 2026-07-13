"""Cadastra convênios de exemplo com preços fixos e percentuais por procedimento.

Uso:
    python manage.py seed_convenios --slug beleza
"""
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError

from core.db_config import ensure_loja_database_config
from superadmin.models import Loja
from tenants.middleware import set_current_loja_id, set_current_tenant_db

# (nome, código)
CONVENIOS_CATALOGO = [
    ("Unimed", "UNIMED"),
    ("Santa Casa", "SANTA-CASA"),
    ("Bradesco Saúde", "BRADESCO"),
]

# (procedimento, modo, valor) — modo: fixo (R$) ou percentual (% do particular)
TABELA_POR_CONVENIO = {
    "Unimed": [
        ("Botox — Testa e Glabela", "fixo", Decimal("700.00")),
        ("Preenchimento Labial", "fixo", Decimal("980.00")),
        ("Harmonização Facial", "fixo", Decimal("2100.00")),
        ("Limpeza de Pele Profunda", "percentual", Decimal("80.00")),
        ("Peeling Químico Suave", "percentual", Decimal("75.00")),
        ("Soroterapia — Imunidade", "percentual", Decimal("80.00")),
        ("Soroterapia — Energia e Foco", "percentual", Decimal("78.00")),
        ("Soroterapia — Detox", "percentual", Decimal("76.00")),
    ],
    "Santa Casa": [
        ("Botox — Testa e Glabela", "fixo", Decimal("500.00")),
        ("Preenchimento Labial", "fixo", Decimal("850.00")),
        ("Harmonização Facial", "fixo", Decimal("1800.00")),
        ("Limpeza de Pele Profunda", "percentual", Decimal("72.00")),
        ("Peeling Químico Suave", "percentual", Decimal("70.00")),
        ("Soroterapia — Imunidade", "percentual", Decimal("71.00")),
        ("Soroterapia — Energia e Foco", "percentual", Decimal("70.00")),
        ("Soroterapia — Detox", "percentual", Decimal("68.00")),
    ],
    "Bradesco Saúde": [
        ("Botox — Testa e Glabela", "fixo", Decimal("650.00")),
        ("Preenchimento Labial", "percentual", Decimal("82.00")),
        ("Harmonização Facial", "percentual", Decimal("78.00")),
        ("Microagulhamento Facial", "percentual", Decimal("85.00")),
        ("Bioestimulador de Colágeno", "fixo", Decimal("1550.00")),
        ("Drenagem Linfática Manual", "percentual", Decimal("90.00")),
    ],
}


class Command(BaseCommand):
    help = "Cadastra convênios com preços fixos e percentuais por procedimento."

    def add_arguments(self, parser):
        parser.add_argument("--slug", default="beleza", help="Slug, atalho ou CNPJ da loja.")

    def _resolver_loja(self, ident: str) -> Loja:
        ident = (ident or "").strip()
        loja = Loja.objects.using("default").filter(slug__iexact=ident).first()
        if not loja:
            loja = Loja.objects.using("default").filter(atalho__iexact=ident).first()
        if not loja:
            so_digitos = "".join(c for c in ident if c.isdigit())
            if so_digitos:
                loja = Loja.objects.using("default").filter(cpf_cnpj=so_digitos).first()
        if not loja:
            raise CommandError(f'Loja não encontrada para "{ident}".')
        return loja

    def handle(self, *args, **options):
        loja = self._resolver_loja(options["slug"])
        if not loja.database_created or not loja.database_name:
            raise CommandError(f"Loja {loja.slug}: schema não criado.")

        db = loja.database_name
        lid = loja.id
        if not ensure_loja_database_config(db, conn_max_age=0):
            raise CommandError("Configure DATABASE_URL (banco da loja inacessível).")

        set_current_loja_id(lid)
        set_current_tenant_db(db)

        from clinica_beleza.models import Convenio, ConvenioProcedimentoPreco, Procedure

        self.stdout.write(self.style.SUCCESS(
            f"\n=== Convênios — {loja.nome} ({loja.slug}) ===\n",
        ))

        proc_por_nome = {
            p.nome: p
            for p in Procedure.objects.using(db).filter(loja_id=lid, is_active=True)
        }
        if not proc_por_nome:
            raise CommandError("Nenhum procedimento ativo. Rode ensure_procedimentos_catalogo antes.")

        precos_criados = 0
        for nome_conv, codigo in CONVENIOS_CATALOGO:
            convenio, created = Convenio.objects.using(db).update_or_create(
                nome=nome_conv,
                loja_id=lid,
                defaults={"codigo": codigo, "is_active": True},
            )
            acao = "criado" if created else "atualizado"
            self.stdout.write(f"   Convênio {nome_conv} ({acao})")

            for proc_nome, modo, valor in TABELA_POR_CONVENIO.get(nome_conv, []):
                proc = proc_por_nome.get(proc_nome)
                if not proc:
                    self.stdout.write(self.style.WARNING(
                        f"      ⚠ Procedimento não encontrado: {proc_nome}",
                    ))
                    continue
                row, _ = ConvenioProcedimentoPreco.objects.using(db).update_or_create(
                    convenio=convenio,
                    procedure=proc,
                    loja_id=lid,
                    defaults={"preco": valor, "modo": modo, "is_active": True},
                )
                efetivo = row.calcular_preco_efetivo(proc)
                precos_criados += 1
                if modo == "percentual":
                    self.stdout.write(
                        f"      · {proc_nome}: {valor}% → R$ {efetivo}",
                    )
                else:
                    self.stdout.write(f"      · {proc_nome}: R$ {valor} (fixo)")

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ {len(CONVENIOS_CATALOGO)} convênios, {precos_criados} regras cadastradas.",
        ))
        self.stdout.write(
            "   O convênio Particular é criado pelo catálogo padrão (ensure_procedimentos_catalogo).\n",
        )
