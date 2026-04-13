"""
Emite uma NFS-e de teste via ISSNet usando a CRMConfig da loja (producao).

Uso no Heroku (exemplo):
  heroku run "cd backend && python manage.py test_emitir_issnet --slug=41449198000172" -a lwksistemas

Requisitos: loja com provedor_nf=issnet, certificado e credenciais salvos;
DATABASE_URL e demais vars de producao carregadas (como no dyno).
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from superadmin.models import Loja
from tenants.middleware import _configure_tenant_db_for_loja


class Command(BaseCommand):
    help = 'Emite NFS-e de teste (valor baixo) via ISSNet para a loja informada.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--slug',
            type=str,
            default='41449198000172',
            help='Slug da loja (ex.: CNPJ sem formatacao)',
        )
        parser.add_argument(
            '--valor',
            type=str,
            default='1.00',
            help='Valor dos servicos (decimal string)',
        )
        parser.add_argument(
            '--sem-email',
            action='store_true',
            help='Nao enviar e-mail ao tomador apos sucesso',
        )

    def handle(self, *args, **options):
        slug = (options['slug'] or '').strip()
        if not slug:
            self.stderr.write('Informe --slug')
            return

        loja = (
            Loja.objects.filter(slug__iexact=slug).first()
            or Loja.objects.filter(cpf_cnpj__icontains=slug.replace('.', '').replace('/', '')).first()
        )
        if not loja:
            self.stderr.write(self.style.ERROR(f'Loja nao encontrada: {slug}'))
            return

        _configure_tenant_db_for_loja(loja, request=None)

        from crm_vendas.models import CRMConfig

        cfg = CRMConfig.get_or_create_for_loja(loja.id)
        if (cfg.provedor_nf or '') != 'issnet':
            self.stderr.write(
                self.style.ERROR(
                    f"Provedor NF da loja e '{cfg.provedor_nf}', nao 'issnet'. Ajuste em CRM > Nota fiscal."
                )
            )
            return

        from nfse_integration.service import NFSeService

        service = NFSeService(loja)
        valor = Decimal(str(options['valor']))

        self.stdout.write(
            f"Loja={loja.nome} id={loja.id} slug={loja.slug} schema={getattr(loja, 'database_name', '')}"
        )
        self.stdout.write('Chamando ISSNet (producao)...')

        resultado = service.emitir_nfse(
            tomador_cpf_cnpj='24758458000172',
            tomador_nome='LWK SISTEMAS LTDA',
            tomador_email='',
            tomador_endereco={
                'logradouro': 'MARCOS MARKARIAN',
                'numero': '1025',
                'bairro': 'NOVA ALIANCA',
                'cidade': 'Ribeirao Preto',
                'uf': 'SP',
                'cep': '14026583',
            },
            servico_descricao='Teste emissao NFS-e (manage.py test_emitir_issnet)',
            valor_servicos=valor,
            numero_rps=None,
            enviar_email=not options['sem_email'],
        )

        if resultado.get('success'):
            self.stdout.write(self.style.SUCCESS(str(resultado)))
        else:
            self.stderr.write(self.style.ERROR(str(resultado.get('error', resultado))))

