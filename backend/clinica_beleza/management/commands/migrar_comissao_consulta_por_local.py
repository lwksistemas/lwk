"""Replica regra geral de comissão de consulta para cada local de atendimento ativo.

Uso:
    python manage.py migrar_comissao_consulta_por_local --slug beleza
    python manage.py migrar_comissao_consulta_por_local --slug beleza --nome "Luiz"
"""
from django.core.management.base import BaseCommand, CommandError

from core.db_config import ensure_loja_database_config
from superadmin.models import Loja
from tenants.middleware import set_current_loja_id, set_current_tenant_db


class Command(BaseCommand):
    help = "Converte comissão de consulta geral em regras por local de atendimento."

    def add_arguments(self, parser):
        parser.add_argument("--slug", default="beleza")
        parser.add_argument("--nome", default="", help="Filtrar profissional pelo nome (opcional).")

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
        from clinica_beleza.models import LocalAtendimento, Professional, ProfessionalCommission

        loja = self._resolver_loja(options["slug"])
        if not loja.database_created or not loja.database_name:
            raise CommandError(f"Loja {loja.slug}: schema não criado.")

        db = loja.database_name
        lid = loja.id
        if not ensure_loja_database_config(db, conn_max_age=0):
            raise CommandError("Configure DATABASE_URL (banco da loja inacessível).")

        set_current_loja_id(lid)
        set_current_tenant_db(db)

        locais = list(
            LocalAtendimento.objects.using(db).filter(loja_id=lid, is_active=True).order_by("nome"),
        )
        if not locais:
            raise CommandError("Nenhum local de atendimento ativo encontrado.")

        profs = Professional.objects.using(db).filter(loja_id=lid, is_active=True)
        nome_filtro = (options.get("nome") or "").strip()
        if nome_filtro:
            profs = profs.filter(nome__icontains=nome_filtro)

        total_criadas = 0
        total_desativadas = 0

        for prof in profs:
            regra_geral = ProfessionalCommission.objects.using(db).filter(
                professional=prof,
                tipo="consulta",
                local_atendimento__isnull=True,
                is_active=True,
            ).first()
            if not regra_geral:
                continue

            ja_tem_local = ProfessionalCommission.objects.using(db).filter(
                professional=prof,
                tipo="consulta",
                local_atendimento__isnull=False,
                is_active=True,
            ).exists()
            if ja_tem_local:
                self.stdout.write(
                    self.style.WARNING(f"   • {prof.nome}: já tem regras por local — ignorado"),
                )
                continue

            for local in locais:
                ProfessionalCommission.objects.using(db).update_or_create(
                    professional=prof,
                    tipo="consulta",
                    procedure=None,
                    local_atendimento=local,
                    loja_id=lid,
                    defaults={
                        "modo": regra_geral.modo,
                        "valor": regra_geral.valor,
                        "is_active": True,
                    },
                )
                total_criadas += 1

            regra_geral.is_active = False
            regra_geral.save(using=db, update_fields=["is_active"])
            total_desativadas += 1
            self.stdout.write(
                f"   • {prof.nome}: {len(locais)} local(is) — "
                f"{regra_geral.modo} {regra_geral.valor}",
            )

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ {total_criadas} regra(s) criada(s), {total_desativadas} regra(s) geral(is) desativada(s).",
        ))
