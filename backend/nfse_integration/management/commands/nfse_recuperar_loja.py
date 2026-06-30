"""Recupera NFS-e do ISSNet no contexto de uma loja (operação/admin)."""
from django.core.management.base import BaseCommand

from superadmin.models import Loja
from tenants.middleware import _configure_tenant_db_for_loja


class Command(BaseCommand):
    help = 'Recupera NFS-e emitida no ISSNet e grava/atualiza no CRM da loja.'

    def add_arguments(self, parser):
        parser.add_argument('--slug', required=True, help='Slug da loja (ex.: felix)')
        parser.add_argument('--numero-nf', required=True, help='Número da NFS-e')
        parser.add_argument('--numero-rps', type=int, default=0, help='Número do RPS (opcional)')
        parser.add_argument('--tomador-nome', default='', help='Forçar nome do tomador após consulta')
        parser.add_argument('--tomador-cnpj', default='', help='Forçar CPF/CNPJ do tomador após consulta')
        parser.add_argument('--tomador-email', default='', help='Forçar e-mail do tomador após consulta')

    def handle(self, *args, **options):
        slug = (options['slug'] or '').strip()
        numero_nf = (options['numero_nf'] or '').strip()
        numero_rps = int(options['numero_rps'] or 0) or None

        loja = Loja.objects.filter(slug__iexact=slug).first()
        if not loja:
            self.stderr.write(self.style.ERROR(f'Loja não encontrada: {slug}'))
            return

        _configure_tenant_db_for_loja(loja)
        from nfse_integration.loja_nfse_api import recuperar_nfse_issnet_loja
        from nfse_integration.persistencia_nfse_loja import atualizar_nfse_recuperada
        from nfse_integration.models import NFSe

        body, status = recuperar_nfse_issnet_loja(
            loja,
            loja.id,
            numero_nf=numero_nf,
            numero_rps=numero_rps,
        )
        self.stdout.write(f'HTTP {status}: {body.get("message") or body.get("error")}')

        tomador_nome = (options.get('tomador_nome') or '').replace('+', ' ').strip()
        overrides = {
            k: v
            for k, v in (
                ('tomador_nome', tomador_nome),
                ('tomador_cpf_cnpj', options.get('tomador_cnpj')),
                ('tomador_email', options.get('tomador_email')),
            )
            if (v or '').strip()
        }
        if overrides:
            nf = NFSe.objects.filter(loja_id=loja.id, numero_nf=numero_nf).first()
            if nf:
                patch = dict(overrides)
                if patch.get('tomador_cpf_cnpj'):
                    from core.cpf_utils import normalizar_cpf_cnpj

                    patch['tomador_cpf_cnpj'] = normalizar_cpf_cnpj(patch['tomador_cpf_cnpj'])
                nf = atualizar_nfse_recuperada(nf, patch, loja=loja)
                self.stdout.write(self.style.WARNING(f'Overrides aplicados: {patch}'))

        nf = NFSe.objects.filter(loja_id=loja.id, numero_nf=numero_nf).first()
        if nf:
            self.stdout.write(
                f'NF {nf.numero_nf} | RPS {nf.numero_rps} | valor {nf.valor} | '
                f'tomador {nf.tomador_nome!r} | doc {nf.tomador_cpf_cnpj}'
            )
