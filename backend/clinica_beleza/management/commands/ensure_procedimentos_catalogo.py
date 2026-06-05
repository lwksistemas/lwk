"""
Garante locais de atendimento e procedimentos com nomes reais no catálogo da loja.

Uso:
    python manage.py ensure_procedimentos_catalogo --slug beleza
"""
from django.core.management.base import BaseCommand, CommandError

from clinica_beleza.procedimentos_catalogo import LOCAIS_CATALOGO, PROCEDIMENTOS_CATALOGO
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja
from tenants.middleware import set_current_loja_id, set_current_tenant_db


class Command(BaseCommand):
    help = 'Cadastra/atualiza locais e procedimentos reais no catálogo da loja (sem apagar atendimentos).'

    def add_arguments(self, parser):
        parser.add_argument('--slug', default='beleza', help='Slug, atalho ou CNPJ da loja.')

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

    def handle(self, *args, **options):
        loja = self._resolver_loja(options['slug'])
        if not loja.database_created or not loja.database_name:
            raise CommandError(f'Loja {loja.slug}: schema não criado.')

        db = loja.database_name
        lid = loja.id
        if not ensure_loja_database_config(db, conn_max_age=0):
            raise CommandError('Configure DATABASE_URL (banco da loja inacessível).')

        set_current_loja_id(lid)
        set_current_tenant_db(db)

        from clinica_beleza.models import LocalAtendimento, Procedure

        self.stdout.write(self.style.SUCCESS(
            f'\n=== Catálogo — {loja.nome} ({loja.slug}) ===\n'
        ))

        for nome, valor in LOCAIS_CATALOGO:
            LocalAtendimento.objects.using(db).update_or_create(
                nome=nome, loja_id=lid,
                defaults={'valor_consulta': valor, 'is_active': True},
            )
        self.stdout.write(f'   {len(LOCAIS_CATALOGO)} locais de atendimento')

        for nome, cat, preco, duracao in PROCEDIMENTOS_CATALOGO:
            Procedure.objects.using(db).update_or_create(
                nome=nome, loja_id=lid,
                defaults={
                    'preco': preco,
                    'duracao_minutos': duracao,
                    'categoria': cat,
                    'is_active': True,
                    'descricao': nome,
                },
            )
        self.stdout.write(f'   {len(PROCEDIMENTOS_CATALOGO)} procedimentos')

        self.stdout.write(self.style.SUCCESS('\n✅ Catálogo atualizado (agenda e nova consulta).'))
