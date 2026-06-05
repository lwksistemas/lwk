"""
Preenche CPF válido (fictício) para pacientes sem CPF cadastrado.

Uso:
    python manage.py preencher_cpf_pacientes --slug beleza
    python manage.py preencher_cpf_pacientes --slug beleza --somente-seed
    python manage.py preencher_cpf_pacientes --slug beleza --forcar
"""
import re

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from clinica_beleza.procedimentos_catalogo import PACIENTES_CATALOGO
from core.db_config import ensure_loja_database_config
from core.validators import formatar_cpf, gerar_cpf_valido
from superadmin.models import Loja
from tenants.middleware import set_current_loja_id, set_current_tenant_db

SEED_TAG = '@seed-comissoes-diverso.lwksistemas.com.br'


class Command(BaseCommand):
    help = 'Atribui CPF de teste válido a pacientes sem CPF na loja.'

    def add_arguments(self, parser):
        parser.add_argument('--slug', default='beleza')
        parser.add_argument(
            '--somente-seed',
            action='store_true',
            help='Aplica só aos pacientes do seed (email @seed-comissoes-diverso).',
        )
        parser.add_argument(
            '--forcar',
            action='store_true',
            help='Substitui CPF existente (cuidado em produção).',
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

    def handle(self, *args, **options):
        from clinica_beleza.models import Patient

        loja = self._resolver_loja(options['slug'])
        if not loja.database_created or not loja.database_name:
            raise CommandError(f'Loja {loja.slug}: schema não criado.')

        db = loja.database_name
        lid = loja.id
        if not ensure_loja_database_config(db, conn_max_age=0):
            raise CommandError('Configure DATABASE_URL (banco da loja inacessível).')

        set_current_loja_id(lid)
        set_current_tenant_db(db)

        qs = Patient.objects.using(db).filter(loja_id=lid, is_active=True)
        if options['somente_seed']:
            qs = qs.filter(email__endswith=SEED_TAG)
        elif not options['forcar']:
            qs = qs.filter(Q(cpf__isnull=True) | Q(cpf=''))

        cpf_por_email_seed = {
            f'paciente{i + 1:02d}{SEED_TAG}': cpf
            for i, (_, _, cpf) in enumerate(PACIENTES_CATALOGO)
        }

        usados = {
            re.sub(r'\D', '', c)
            for c in Patient.objects.using(db)
            .filter(loja_id=lid)
            .exclude(Q(cpf__isnull=True) | Q(cpf=''))
            .values_list('cpf', flat=True)
        }

        atualizados = 0
        for pac in qs.order_by('id'):
            if pac.cpf and not options['forcar']:
                continue

            cpf_fmt = cpf_por_email_seed.get(pac.email or '')
            if not cpf_fmt:
                seed = (pac.id or 0) * 997 + lid
                for attempt in range(300):
                    candidato = formatar_cpf(gerar_cpf_valido(seed + attempt))
                    digitos = re.sub(r'\D', '', candidato)
                    if digitos not in usados:
                        cpf_fmt = candidato
                        break
                else:
                    self.stdout.write(self.style.WARNING(f'   • {pac.nome}: sem CPF livre'))
                    continue

            digitos = re.sub(r'\D', '', cpf_fmt)
            if digitos in usados and not options['forcar']:
                continue

            pac.cpf = cpf_fmt
            pac.save(using=db, update_fields=['cpf'])
            usados.add(digitos)
            atualizados += 1
            self.stdout.write(f'   • {pac.nome}: {cpf_fmt}')

        self.stdout.write(self.style.SUCCESS(f'\n✅ {atualizados} paciente(s) atualizado(s).'))
