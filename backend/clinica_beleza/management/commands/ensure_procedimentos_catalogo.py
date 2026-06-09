"""
Garante locais de atendimento e procedimentos padrão de estética no catálogo da loja.

Uso:
    python manage.py ensure_procedimentos_catalogo --slug novaimagem
    python manage.py ensure_procedimentos_catalogo --all-clinica-beleza
"""
from django.core.management.base import BaseCommand, CommandError

from clinica_beleza.procedimentos_catalogo import (
    LOCAIS_CATALOGO,
    PROCEDIMENTOS_CATALOGO,
    procedimento_catalogo_defaults,
)
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja
from tenants.middleware import set_current_loja_id, set_current_tenant_db

TIPO_CLINICA_BELEZA = 'Clínica da Beleza'


class Command(BaseCommand):
    help = (
        'Cadastra/atualiza locais e procedimentos padrão de estética '
        '(descrição + TCLE quando aplicável) sem apagar atendimentos.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--slug', help='Slug, atalho ou CNPJ da loja.')
        parser.add_argument(
            '--all-clinica-beleza',
            action='store_true',
            help='Aplica em todas as lojas ativas do tipo Clínica da Beleza.',
        )

    def _resolver_loja(self, ident: str) -> Loja:
        ident = (ident or '').strip()
        loja = Loja.objects.using('default').filter(slug__iexact=ident).first()
        if not loja:
            loja = Loja.objects.using('default').filter(atalho__iexact=ident).first()
        if not loja:
            so_digitos = ''.join(c for c in ident if c.isdigit())
            if so_digitos:
                loja = Loja.objects.using('default').filter(cpf_cnpj=so_digitos).first()
        if not loja:
            raise CommandError(f'Loja não encontrada para "{ident}".')
        return loja

    def _lojas_alvo(self, options) -> list[Loja]:
        if options.get('all_clinica_beleza'):
            return list(
                Loja.objects.using('default')
                .filter(is_active=True, database_created=True, tipo_loja__nome=TIPO_CLINICA_BELEZA)
                .select_related('tipo_loja')
                .order_by('slug')
            )
        slug = (options.get('slug') or '').strip()
        if not slug:
            raise CommandError('Informe --slug ou --all-clinica-beleza.')
        return [self._resolver_loja(slug)]

    def _aplicar_catalogo(self, loja: Loja) -> None:
        if not loja.database_created or not loja.database_name:
            self.stdout.write(self.style.WARNING(f'  skip {loja.slug}: schema não criado'))
            return

        db = loja.database_name
        lid = loja.id
        if not ensure_loja_database_config(db, conn_max_age=0):
            self.stdout.write(self.style.WARNING(f'  skip {loja.slug}: banco inacessível'))
            return

        set_current_loja_id(lid)
        set_current_tenant_db(db)

        from clinica_beleza.models import LocalAtendimento, Procedure

        self.stdout.write(self.style.SUCCESS(f'\n=== Catálogo — {loja.nome} ({loja.slug}) ==='))

        for nome, valor in LOCAIS_CATALOGO:
            LocalAtendimento.objects.using(db).update_or_create(
                nome=nome, loja_id=lid,
                defaults={'valor_consulta': valor, 'is_active': True},
            )
        self.stdout.write(f'   {len(LOCAIS_CATALOGO)} locais de atendimento')

        com_termo = 0
        for item in PROCEDIMENTOS_CATALOGO:
            defaults = procedimento_catalogo_defaults(item)
            if defaults['termo_consentimento_ativo']:
                com_termo += 1
            Procedure.objects.using(db).update_or_create(
                nome=item.nome, loja_id=lid,
                defaults=defaults,
            )
        self.stdout.write(
            f'   {len(PROCEDIMENTOS_CATALOGO)} procedimentos '
            f'({com_termo} com termo de consentimento)'
        )

    def handle(self, *args, **options):
        lojas = self._lojas_alvo(options)
        if not lojas:
            self.stdout.write(self.style.WARNING('Nenhuma loja Clínica da Beleza encontrada.'))
            return

        for loja in lojas:
            self._aplicar_catalogo(loja)

        self.stdout.write(self.style.SUCCESS('\n✅ Catálogo padrão de estética atualizado.'))
