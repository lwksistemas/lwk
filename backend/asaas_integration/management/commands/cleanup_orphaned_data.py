"""
Comando Django para limpar dados órfãos do Asaas
Uso: python manage.py cleanup_orphaned_data
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from asaas_integration.models import AsaasPayment, AsaasCustomer, LojaAssinatura
from superadmin.models import Loja

class Command(BaseCommand):
    help = 'Limpa dados órfãos do Asaas (pagamentos, clientes e assinaturas sem lojas associadas)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostra o que seria removido, sem executar',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Executa sem confirmação',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🧹 Iniciando limpeza de dados órfãos do Asaas...')
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
        
        # 3. Confirmar ou executar
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('🔍 DRY RUN - Nenhum dado foi removido')
            )
            return
        
        if not options['force']:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️ ATENÇÃO: Serão removidos {len(pagamentos_orfaos)} pagamentos '
                    f'totalizando R$ {total_valor:.2f}'
                )
            )
            self.stdout.write('Esta operação é IRREVERSÍVEL!')
            
            confirmacao = input('Deseja continuar? (digite "SIM" para confirmar): ')
            if confirmacao.upper() != 'SIM':
                self.stdout.write(
                    self.style.ERROR('❌ Operação cancelada pelo usuário.')
                )
                return
        
        # 4. Executar limpeza
        with transaction.atomic():
            resultado = self.limpar_dados_locais(pagamentos_orfaos, clientes_orfaos, assinaturas_orfas)
        
        # 5. Verificar resultado
        self.verificar_limpeza()
        
        # 6. Resumo final
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('RESUMO DA LIMPEZA')
        self.stdout.write('=' * 60)
        self.stdout.write(f'💰 Valor total removido: R$ {total_valor:.2f}')
        self.stdout.write(f'📋 Assinaturas removidas: {resultado["assinaturas_removidas"]}')
        self.stdout.write(f'💳 Pagamentos removidos: {resultado["pagamentos_removidos"]}')
        self.stdout.write(f'👤 Clientes removidos: {resultado["clientes_removidos"]}')
        
        self.stdout.write(
            self.style.SUCCESS('\n🎉 LIMPEZA CONCLUÍDA COM SUCESSO!')
        )
        self.stdout.write('✅ Sistema financeiro está limpo e pronto para uso.')

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

    def limpar_dados_locais(self, pagamentos_orfaos, clientes_orfaos, assinaturas_orfas):
        """Limpar dados órfãos do banco local"""
        self.stdout.write('\n🧹 Limpando dados órfãos do banco local...')
        
        # 1. Remover assinaturas órfãs
        assinaturas_removidas = 0
        for assinatura in assinaturas_orfas:
            self.stdout.write(f'🗑️ Removendo assinatura: {assinatura.loja_slug}')
            assinatura.delete()
            assinaturas_removidas += 1
        
        # 2. Remover pagamentos órfãos
        pagamentos_removidos = 0
        for payment in pagamentos_orfaos:
            self.stdout.write(f'🗑️ Removendo pagamento: {payment.asaas_id} (R$ {payment.value})')
            payment.delete()
            pagamentos_removidos += 1
        
        # 3. Remover clientes órfãos
        clientes_removidos = 0
        for customer in clientes_orfaos:
            self.stdout.write(f'🗑️ Removendo cliente: {customer.asaas_id} ({customer.name})')
            customer.delete()
            clientes_removidos += 1
        
        return {
            'assinaturas_removidas': assinaturas_removidas,
            'pagamentos_removidos': pagamentos_removidos,
            'clientes_removidos': clientes_removidos
        }

    def verificar_limpeza(self):
        """Verificar se a limpeza foi bem-sucedida"""
        self.stdout.write('\n🔍 Verificando resultado da limpeza...')
        
        pagamentos_restantes = AsaasPayment.objects.count()
        clientes_restantes = AsaasCustomer.objects.count()
        assinaturas_restantes = LojaAssinatura.objects.count()
        
        self.stdout.write(f'📊 Dados restantes:')
        self.stdout.write(f'   - Pagamentos: {pagamentos_restantes}')
        self.stdout.write(f'   - Clientes: {clientes_restantes}')
        self.stdout.write(f'   - Assinaturas: {assinaturas_restantes}')
        
        if pagamentos_restantes == 0 and clientes_restantes == 0 and assinaturas_restantes == 0:
            self.stdout.write(
                self.style.SUCCESS('✅ Limpeza completa! Todos os dados órfãos foram removidos.')
            )
            return True
        else:
            self.stdout.write(
                self.style.WARNING('⚠️ Ainda existem dados no sistema. Verificar se são legítimos.')
            )
            return False