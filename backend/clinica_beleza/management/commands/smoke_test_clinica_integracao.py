"""Smoke tests de integração no schema PostgreSQL real da loja (não usa banco de testes Django).

Loja de testes em produção: **vida** (https://lwksistemas.com.br/loja/vida/dashboard)

Preferir staging/beta para --write. Testes com escrita usam rollback automático no tenant (--write).

Uso local (DATABASE_URL pública ou `railway connect` — internal *.railway.internal não resolve fora da rede Railway):
  cd backend
  export DJANGO_SETTINGS_MODULE=config.settings_production
  python manage.py smoke_test_clinica_integracao --slug vida --allow-production

Após deploy do backend (comando precisa existir na imagem):
  railway ssh -s lwks-backend -- python manage.py smoke_test_clinica_integracao --slug vida --allow-production
  railway ssh -s lwks-backend -- python manage.py smoke_test_clinica_integracao --slug vida --write --allow-production

Railway staging:
  railway run --environment staging --service lwks-backend-staging \\
    sh -c 'cd backend && DJANGO_SETTINGS_MODULE=config.settings_production python manage.py smoke_test_clinica_integracao --slug vida --write'
"""
import os
import sys

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from clinica_beleza.smoke_integracao import SmokeContext, run_smoke_checks
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja
from tenants.middleware import set_current_loja_id, set_current_tenant_db


class Command(BaseCommand):
    help = "Smoke tests Clínica da Beleza no schema tenant real (PostgreSQL)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--slug",
            required=True,
            help="Slug, atalho ou CNPJ da loja (produção teste: vida).",
        )
        parser.add_argument(
            "--slug-b",
            default="",
            help="Segunda loja para testes de isolamento (opcional).",
        )
        parser.add_argument(
            "--write",
            action="store_true",
            help="Inclui testes que gravam dados ([SMOKE] …) com rollback no schema tenant.",
        )
        parser.add_argument(
            "--no-rollback",
            action="store_true",
            help="Com --write, persiste dados (não usar em produção).",
        )
        parser.add_argument(
            "--allow-production",
            action="store_true",
            help="Permite execução mesmo com host de produção (use com cuidado).",
        )

    def _resolver_loja(self, ident: str) -> Loja:
        ident = (ident or "").strip()
        if not ident:
            raise CommandError("Identificador da loja vazio.")
        loja = Loja.objects.using("default").filter(slug__iexact=ident).first()
        if not loja:
            loja = Loja.objects.using("default").filter(atalho__iexact=ident).first()
        if not loja:
            digits = "".join(c for c in ident if c.isdigit())
            if digits:
                loja = Loja.objects.using("default").filter(cpf_cnpj=digits).first()
        if not loja:
            raise CommandError(f'Loja não encontrada para "{ident}".')
        return loja

    def _assert_postgres(self) -> None:
        engine = (settings.DATABASES.get("default") or {}).get("ENGINE", "")
        if "postgresql" not in engine:
            raise CommandError(
                "Este comando exige PostgreSQL (schema loja_*). "
                "Defina DATABASE_URL e DJANGO_SETTINGS_MODULE=config.settings_production. "
                "Para testes locais SQLite use: python manage.py test clinica_beleza.tests.test_integracao_tenant",
            )
        if not os.environ.get("DATABASE_URL"):
            raise CommandError("DATABASE_URL não configurada.")

    def _warn_production(self, allow_production: bool) -> None:
        url = (os.environ.get("DATABASE_URL") or "").lower()
        hosts = " ".join(getattr(settings, "ALLOWED_HOSTS", [])).lower()
        looks_prod = (
            "lwksistemas.com.br" in hosts
            or "api.lwksistemas.com.br" in hosts
        ) and "staging" not in url and "beta" not in url
        if looks_prod and not allow_production:
            raise CommandError(
                "Ambiente parece produção. Use staging/beta ou passe --allow-production "
                "(somente leitura recomendado; --write grava mesmo com rollback parcial via API).",
            )

    def _configure_loja(self, loja: Loja) -> str:
        if not loja.database_created or not loja.database_name:
            raise CommandError(f"Loja {loja.slug}: schema não criado (database_created=False).")
        if loja.tipo_loja.slug != "clinica-beleza":
            raise CommandError(
                f'Loja {loja.slug} é tipo "{loja.tipo_loja.slug}", esperado clinica-beleza.',
            )
        if not ensure_loja_database_config(loja.database_name, conn_max_age=0):
            raise CommandError(
                f'Não foi possível configurar conexão tenant "{loja.database_name}".',
            )
        return loja.database_name

    def handle(self, *args, **options):
        self._assert_postgres()
        self._warn_production(options["allow_production"])

        loja = self._resolver_loja(options["slug"])
        tenant_a = self._configure_loja(loja)

        loja_b = None
        tenant_b = None
        if options.get("slug_b"):
            loja_b = self._resolver_loja(options["slug_b"])
            tenant_b = self._configure_loja(loja_b)

        if not loja.owner_id:
            raise CommandError(f"Loja {loja.slug} sem owner.")

        ctx = SmokeContext(
            loja_id=loja.id,
            loja_slug=loja.slug,
            tenant_db=tenant_a,
            owner=loja.owner,
            loja_b_id=loja_b.id if loja_b else None,
            loja_b_slug=loja_b.slug if loja_b else None,
            loja_b_tenant_db=tenant_b,
        )

        self.stdout.write("")
        self.stdout.write("=" * 72)
        self.stdout.write(
            f"SMOKE Clínica da Beleza — {loja.nome} ({loja.slug}) → schema {tenant_a}",
        )
        if loja_b:
            self.stdout.write(f"  Loja B: {loja_b.nome} ({loja_b.slug}) → {tenant_b}")
        mode = "leitura + escrita (rollback)" if options["write"] and not options["no_rollback"] else (
            "leitura + escrita (SEM rollback)" if options["write"] else "somente leitura"
        )
        self.stdout.write(f"  Modo: {mode}")
        self.stdout.write("=" * 72)

        results = run_smoke_checks(
            ctx,
            include_write=options["write"],
            rollback_write=not options["no_rollback"],
        )

        failed = 0
        for name, err in results:
            if err is None:
                self.stdout.write(self.style.SUCCESS(f"  OK  {name}"))
            else:
                failed += 1
                self.stdout.write(self.style.ERROR(f"  FAIL {name}: {err}"))

        self.stdout.write("")
        if failed:
            self.stdout.write(self.style.ERROR(f"❌ {failed} falha(s) de {len(results)}"))
            sys.exit(1)

        self.stdout.write(self.style.SUCCESS(f"✅ {len(results)} checks OK"))
        set_current_tenant_db("default")
        set_current_loja_id(None)
