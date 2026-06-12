"""
Teste end-to-end: cadastro loja → webhook pagamento → senha + NFS-e.

Uso (produção):
  python manage.py teste_fluxo_cadastro_asaas --simulate-webhook
"""
import uuid

from django.core.management.base import BaseCommand, CommandError

from superadmin.models import Loja, NFSeEmitida


class Command(BaseCommand):
    help = 'Cria loja teste e valida fluxo pós-pagamento Asaas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--simulate-webhook',
            action='store_true',
            help='Simula PAYMENT_RECEIVED no webhook (sem PIX real)',
        )
        parser.add_argument(
            '--email',
            default='pjluiz25@hotmail.com',
            help='E-mail do administrador da loja teste',
        )

    def handle(self, *args, **options):
        from superadmin.serializers import LojaCreateSerializer
        from superadmin.sync_service import AsaasSyncService
        from asaas_integration.models import AsaasConfig

        suffix = uuid.uuid4().hex[:8]
        cnpj_digits = f'41449198{suffix[:4]}73'[:14].ljust(14, '0')
        atalho = f'clinica-teste-{suffix}'

        payload = {
            'nome': f'Clinica Teste Fluxo {suffix}',
            'cpf_cnpj': cnpj_digits,
            'atalho': atalho,
            'cep': '14010-100',
            'logradouro': 'Rua General Osorio',
            'numero': '500',
            'bairro': 'Centro',
            'cidade': 'Ribeirao Preto',
            'uf': 'SP',
            'tipo_loja': 7,
            'plano': 11,
            'tipo_assinatura': 'mensal',
            'provedor_boleto_preferido': 'asaas',
            'forma_pagamento_preferida': 'boleto',
            'owner_full_name': 'Felipe Teste Fluxo',
            'owner_username': f'felipe_teste_{suffix}',
            'owner_email': options['email'],
            'owner_telefone': '16987654321',
            'dia_vencimento': 10,
        }

        self.stdout.write('1/4 Criando loja teste…')
        ser = LojaCreateSerializer(data=payload)
        if not ser.is_valid():
            raise CommandError(str(ser.errors))
        loja = ser.save()

        financeiro = loja.financeiro
        payment_id = (financeiro.asaas_payment_id or '').strip()
        self.stdout.write(self.style.SUCCESS(
            f'   Loja #{loja.id} slug={loja.slug} atalho=/{atalho}/'
        ))
        self.stdout.write(f'   Asaas payment: {payment_id or "—"}')
        self.stdout.write(f'   Boleto: {(financeiro.boleto_url or "")[:70]}…')
        self.stdout.write(f'   Status: {financeiro.status_pagamento}')

        if not payment_id:
            raise CommandError('Cobrança Asaas não foi criada — verifique API conectada')

        if options['simulate_webhook']:
            self.stdout.write('2/4 Simulando webhook PAYMENT_RECEIVED…')
            sync = AsaasSyncService()
            resultado = sync.process_webhook_payment({
                'id': payment_id,
                'event': 'PAYMENT_RECEIVED',
                'status': 'RECEIVED',
                'value': float(financeiro.valor_mensalidade or 8),
                'billingType': 'PIX',
                'externalReference': f'loja_{loja.slug}_assinatura',
                'description': f'Assinatura teste {loja.nome}',
            })
            self.stdout.write(f'   Webhook: {resultado}')

        else:
            self.stdout.write('2/4 Consultando status no Asaas…')
            sync = AsaasSyncService()
            res = sync.asaas_service.consultar_status_pagamento(payment_id)
            self.stdout.write(f'   Status Asaas: {res.get("status")}')
            if res.get('status') in ('RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH'):
                sync._process_payment_confirmed(
                    loja, financeiro, payment_id, res.get('raw_payment') or {},
                )
            else:
                self.stdout.write(self.style.WARNING(
                    '   PIX ainda pendente — pague o boleto/PIX e rode:\n'
                    f'   python manage.py confirmar_pagamento_loja {atalho} --atalho'
                ))

        financeiro.refresh_from_db()
        loja.refresh_from_db()

        self.stdout.write('3/4 Verificando senha provisória…')
        self.stdout.write(
            f'   status_pagamento={financeiro.status_pagamento} '
            f'senha_enviada={financeiro.senha_enviada}'
        )

        self.stdout.write('4/4 Verificando NFS-e…')
        nf = NFSeEmitida.objects.filter(pagamento__loja=loja).order_by('-id').first()
        if nf:
            self.stdout.write(f'   NFS-e #{nf.id} status={nf.status} numero={nf.numero_nf or "—"}')
        else:
            self.stdout.write('   NFS-e: nenhuma emitida ainda')

        api_ok = bool(AsaasConfig.resolve_api_key())
        webhook_ok = len(AsaasConfig.resolve_webhook_token()) >= 32
        self.stdout.write('')
        self.stdout.write(f'API Asaas: {"OK" if api_ok else "FALHA"}')
        self.stdout.write(f'Webhook token: {"OK" if webhook_ok else "FALHA"}')
        self.stdout.write(f'URL login: https://lwksistemas.com.br/{atalho}/login')
        if financeiro.boleto_url:
            self.stdout.write(f'PIX/Boleto: {financeiro.boleto_url}')

        ok = financeiro.status_pagamento == 'ativo' and financeiro.senha_enviada
        if ok:
            self.stdout.write(self.style.SUCCESS('\n✅ Fluxo completo OK (pagamento + senha)'))
        else:
            self.stdout.write(self.style.WARNING('\n⚠️ Aguardando pagamento ou reprocessamento'))
