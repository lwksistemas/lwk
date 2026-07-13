"""Garante produtos padrão de estoque (estética + soroterapia) nas lojas Clínica da Beleza.

Uso:
    python manage.py ensure_estoque_catalogo --slug lnfd
    python manage.py ensure_estoque_catalogo --all-clinica-beleza
    python manage.py ensure_estoque_catalogo --slug lnfd --adicionar-faltantes
"""
from django.core.management.base import BaseCommand, CommandError

from clinica_beleza.catalogo_service import lojas_clinica_beleza_com_schema
from clinica_beleza.estoque_catalogo_service import aplicar_estoque_catalogo_padrao
from superadmin.models import Loja


class Command(BaseCommand):
    help = (
        "Cadastra produtos padrão do estoque (soroterapia com nomes comerciais + "
        "insumos de estética) sem apagar cadastros existentes."
    )

    def add_arguments(self, parser):
        parser.add_argument("--slug", help="Slug, atalho ou CNPJ da loja.")
        parser.add_argument(
            "--all-clinica-beleza",
            action="store_true",
            help="Aplica em todas as lojas ativas do tipo Clínica da Beleza.",
        )
        parser.add_argument(
            "--adicionar-faltantes",
            action="store_true",
            help="Inclui itens do catálogo mesmo se a loja já tiver outros produtos.",
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

        adicionar = bool(options.get("adicionar_faltantes"))
        total_itens = 0
        for loja in lojas:
            stats = aplicar_estoque_catalogo_padrao(
                loja,
                log=self.stdout.write,
                adicionar_faltantes=adicionar,
            )
            if stats and not stats.get("ignorado"):
                total_itens += stats.get("produtos", 0)

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Catálogo de estoque aplicado em {len(lojas)} loja(s).",
            ),
        )
