"""
Comando Django para mostrar dados órfãos do Asaas (apenas visualização)
Uso: python manage.py show_orphaned_data
"""
from django.core.management.base import BaseCommand
from asaas_integration.models import AsaasPayment, AsaasCustomer, LojaAssinatura
from superadmin.models import Loja

class Command(BaseCommand):
    help = 'Mostra dados órfãos do Asaas (apenas visualização, não remove nada)'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 Analisando dados órfãos do Asaas...')
        )
        
        # 1. Identificar dados órfãos
        pagamentos_orfaos, clientes_orfaos, assinaturas_orfas = self.identificar_dados_orfaos()
        
        if not pagamentos_orfaos and not clientes_orfaos and not assinaturas_orfas:
            self.stdout.write(
                self.style.SUCCESS('✅ Nenhum dado órfão encontrado! Sistema já está limpo.')
            )
            return
        
        # 2. Mostrar detalhes
        total_valor = self.listar_pagamentos_orfaos(pagamentos_orfaos)
        
        # 3. Resumo
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('RESUMO DOS DADOS ÓRFÃOS')
        self.stdout.write('=' * 60)
        self.stdout.write(f'💰 Valor total em pagamentos órfãos: R$ {total_valor:.2f}')
        self.stdout.write(f'📋 Assinaturas órfãs: {len(assinaturas_orfas)}')
        self.stdout.write(f'💳 Pagamentos órfãos: {len(pagamentos_orfaos)}')
        self.stdout.write(f'👤 Clientes órfãos: {len(clientes_orfaos)}')
        
        self.stdout.write('\n📝 Para remover estes dados, execute:')
        self.stdout.write('python manage.py cleanup_orphaned_data --force')

    def identificar_dados_orfaos(self):
        """Identificar dados órfãos no sistema"""
        self.stdout.write('🔍 Identificando dados órfãos...')
        
        # 1. Pagamentos órfãos
        pagamentos_orfaos = []
        for payment in AsaasPayment.objects.all():
            # Verificar se a loja ainda existe pela external_reference
            if payment.external_reference:
                if 'loja_' in payment.external_reference:
                    loja_slug = payment.external_reference.replace('loja_', '').replace('_assinatura', '').replace('_pix', '')
                    try:
                        Loja.objects.get(slug=loja_slug, is_active=True)
                    except Loja.DoesNotExist:
                        pagamentos_orfaos.append(payment)
            else:
                # Pagamento sem referência - provavelmente órfão
                pagamentos_orfaos.append(payment)
        
        # 2. Clientes órfãos
        clientes_orfaos = []
        for customer in AsaasCustomer.objects.all():
            # Verificar se tem pagamentos associados a lojas existentes
            tem_loja_ativa = False
            for payment in customer.payments.all():
                if payment.external_reference and 'loja_' in payment.external_reference:
                    loja_slug = payment.external_reference.replace('loja_', '').replace('_assinatura', '').replace('_pix', '')
                    try:
                        Loja.objects.get(slug=loja_slug, is_active=True)
                        tem_loja_ativa = True
                        break
                    except Loja.DoesNotExist:
                        continue
            
            if not tem_loja_ativa:
                clientes_orfaos.append(customer)
        
        # 3. Assinaturas órfãs
        assinaturas_orfas = []
        for assinatura in LojaAssinatura.objects.all():
            try:
                Loja.objects.get(slug=assinatura.loja_slug, is_active=True)
            except Loja.DoesNotExist:
                assinaturas_orfas.append(assinatura)
        
        self.stdout.write(f'📊 Dados órfãos encontrados:')
        self.stdout.write(f'   - Pagamentos: {len(pagamentos_orfaos)}')
        self.stdout.write(f'   - Clientes: {len(clientes_orfaos)}')
        self.stdout.write(f'   - Assinaturas: {len(assinaturas_orfas)}')
        
        return pagamentos_orfaos, clientes_orfaos, assinaturas_orfas

    def listar_pagamentos_orfaos(self, pagamentos_orfaos):
        """Listar detalhes dos pagamentos órfãos"""
        if not pagamentos_orfaos:
            return 0
            
        self.stdout.write('\n💰 Detalhes dos pagamentos órfãos:')
        self.stdout.write('-' * 80)
        
        total_valor = 0
        for payment in pagamentos_orfaos:
            self.stdout.write(f'ID: {payment.asaas_id}')
            self.stdout.write(f'Cliente: {payment.customer.name if payment.customer else "N/A"}')
            self.stdout.write(f'Valor: R$ {payment.value}')
            self.stdout.write(f'Status: {payment.status}')
            self.stdout.write(f'Vencimento: {payment.due_date}')
            self.stdout.write(f'Referência: {payment.external_reference}')
            self.stdout.write(f'Criado em: {payment.created_at}')
            self.stdout.write('-' * 40)
            
            total_valor += float(payment.value)
        
        self.stdout.write(f'💸 Total em pagamentos órfãos: R$ {total_valor:.2f}')
        return total_valor