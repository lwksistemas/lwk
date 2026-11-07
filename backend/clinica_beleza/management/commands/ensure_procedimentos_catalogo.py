"""Garante o local padrão da Clínica da Beleza. Não semeia procedimentos.

Uso:
    python manage.py ensure_procedimentos_catalogo --slug novaimagem
    python manage.py ensure_procedimentos_catalogo --all-clinica-beleza
"""
from django.core.management.base import BaseCommand, CommandError

from clinica_beleza.catalogo_service import aplicar_catalogo_padrao, lojas_clinica_beleza_com_schema
from superadmin.models import Loja


class Command(BaseCommand):
    help = (
        "Garante o local padrão. Não cria procedimentos: cada clínica cadastra os seus. "
        "Não reescreve o que a loja já cadastrou."
    )

    def add_arguments(self, parser):
        parser.add_argument("--slug", help="Slug, atalho ou CNPJ da loja.")
        parser.add_argument(
            "--all-clinica-beleza",
            action="store_true",
            help="Aplica em todas as lojas ativas do tipo Clínica da Beleza.",
        )

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

    def _lojas_alvo(self, options) -> list[Loja]:
        if options.get("all_clinica_beleza"):
            return list(lojas_clinica_beleza_com_schema(apenas_ativas=True))
        slug = (options.get("slug") or "").strip()
        if not slug:
            raise CommandError("Informe --slug ou --all-clinica-beleza.")
        return [self._resolver_loja(slug)]

    def handle(self, *args, **options):
        lojas = self._lojas_alvo(options)
        if not lojas:
            self.stdout.write(self.style.WARNING("Nenhuma loja Clínica da Beleza encontrada."))
            return

        for loja in lojas:
            aplicar_catalogo_padrao(loja, log=self.stdout.write)

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Catálogo padrão aplicado em {len(lojas)} loja(s). "
                "Procedimentos não são semeados.",
            ),
        )
