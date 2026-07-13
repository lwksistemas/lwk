"""
Cria regras de comissão de procedimento faltantes para um profissional (não sobrescreve existentes).

Uso:
    python manage.py sync_comissoes_procedimentos --slug beleza --nome "Luiz"
    python manage.py sync_comissoes_procedimentos --slug beleza --nome "Luiz" --modo fixo --valor 50
"""
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError

from clinica_beleza.procedimentos_catalogo import PROCEDIMENTOS_CATALOGO_NOMES
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja
from tenants.middleware import set_current_loja_id, set_current_tenant_db


class Command(BaseCommand):
    help = 'Preenche comissões de procedimento ausentes para o profissional (catálogo ativo).'

    def add_arguments(self, parser):
        parser.add_argument('--slug', default='beleza')
        parser.add_argument('--nome', required=True, help='Parte do nome do profissional.')
        parser.add_argument('--modo', choices=['percentual', 'fixo'], default='percentual')
        parser.add_argument('--valor', default='20', help='Percentual ou valor fixo R$.')
        parser.add_argument(
            '--somente-catalogo',
            action='store_true',
            help='Aplica só aos procedimentos do catálogo padrão (nomes reais).',
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
        loja = self._resolver_loja(options['slug'])
        if not loja.database_created or not loja.database_name:
            raise CommandError(f'Loja {loja.slug}: schema não criado.')

        db = loja.database_name
        lid = loja.id
        if not ensure_loja_database_config(db, conn_max_age=0):
            raise CommandError('Configure DATABASE_URL.')

        set_current_loja_id(lid)
        set_current_tenant_db(db)

        from clinica_beleza.models import Procedure, Professional, ProfessionalCommission

        nome_busca = (options['nome'] or '').strip()
        prof = (
            Professional.objects.using(db)
            .filter(loja_id=lid, is_active=True, nome__icontains=nome_busca)
            .first()
        )
        if not prof:
            raise CommandError(f'Profissional não encontrado contendo "{nome_busca}".')

        try:
            valor = Decimal(str(options['valor']).replace(',', '.'))
        except Exception as exc:
            raise CommandError(f'Valor inválido: {options["valor"]}') from exc

        modo = options['modo']
        procs = Procedure.objects.using(db).filter(loja_id=lid, is_active=True).order_by('nome')
        if options['somente_catalogo']:
            procs = procs.filter(nome__in=PROCEDIMENTOS_CATALOGO_NOMES)

        existentes = set(
            ProfessionalCommission.objects.using(db)
            .filter(professional=prof, tipo='procedimento', is_active=True, procedure_id__isnull=False)
            .values_list('procedure_id', flat=True)
        )

        criados = 0
        for proc in procs:
            if proc.id in existentes:
                continue
            ProfessionalCommission.objects.using(db).create(
                professional=prof,
                tipo='procedimento',
                modo=modo,
                valor=valor,
                procedure=proc,
                loja_id=lid,
                is_active=True,
            )
            criados += 1
            self.stdout.write(f'   + {proc.nome}: {modo} {valor}')

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ {prof.nome}: {criados} regra(s) criada(s), {len(existentes)} já existente(s).'
        ))
