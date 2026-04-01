"""
Comando para identificar e remover clientes duplicados no Asaas

Identifica clientes com mesmo CPF/CNPJ ou email e mantém apenas o mais recente.

Uso:
    python manage.py limpar_clientes_duplicados_asaas
    python manage.py limpar_clientes_duplicados_asaas --dry-run
"""
from django.core.management.base import BaseCommand
from asaas_integration.models import AsaasCustomer, LojaAssinatura
from asaas_integration.client import AsaasClient, AsaasConfig
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Identifica e remove clientes duplicados no Asaas'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula a execução sem remover clientes'
        )
    
    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 Modo DRY-RUN ativado - nenhum cliente será removido\n'))
        
        self.stdout.write(self.style.SUCCESS('🔍 Buscando clientes duplicados no Asaas...'))
        
        # Obter cliente Asaas
        config = AsaasConfig.get_config()
        if not config or not config.api_key:
            self.stdout.write(self.style.ERROR('❌ Asaas não configurado'))
            return
        
        client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)
        
        # Buscar todos os clientes do Asaas
        try:
            self.stdout.write('📥 Buscando clientes da API Asaas...')
            
            all_customers = []
            offset = 0
            limit = 100
            
            while True:
                response = client.list_customers(limit=limit, offset=offset)
                customers = response.get('data', [])
                
                if not customers:
                    break
                
                all_customers.extend(customers)
                offset += limit
                
                if not response.get('hasMore', False):
                    break
            
            self.stdout.write(f'✅ {len(all_customers)} clientes encontrados\n')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao buscar clientes: {e}'))
            return
        
        # Agrupar por CPF/CNPJ e Email
        by_cpf_cnpj = defaultdict(list)
        by_email = defaultdict(list)
        
        for customer in all_customers:
            cpf_cnpj = customer.get('cpfCnpj', '').strip()
            email = customer.get('email', '').strip().lower()
            
            if cpf_cnpj:
                by_cpf_cnpj[cpf_cnpj].append(customer)
            if email:
                by_email[email].append(customer)
        
        # Identificar duplicados
        duplicados_cpf = {k: v for k, v in by_cpf_cnpj.items() if len(v) > 1}
        duplicados_email = {k: v for k, v in by_email.items() if len(v) > 1}
        
        self.stdout.write(f'📊 Duplicados por CPF/CNPJ: {len(duplicados_cpf)}')
        self.stdout.write(f'📊 Duplicados por Email: {len(duplicados_email)}\n')
        
        if not duplicados_cpf and not duplicados_email:
            self.stdout.write(self.style.SUCCESS('✅ Nenhum cliente duplicado encontrado!'))
            return
        
        # Processar duplicados por CPF/CNPJ
        total_removidos = 0
        
        if duplicados_cpf:
            self.stdout.write(self.style.WARNING(f'\n🔍 Processando {len(duplicados_cpf)} grupos de duplicados por CPF/CNPJ...\n'))
            
            for cpf_cnpj, customers in duplicados_cpf.items():
                self.stdout.write(f'📋 CPF/CNPJ: {cpf_cnpj}')
                self.stdout.write(f'   {len(customers)} clientes encontrados:')
                
                # Ordenar por data de criação (mais recente primeiro)
                customers_sorted = sorted(
                    customers,
                    key=lambda x: x.get('dateCreated', ''),
                    reverse=True
                )
                
                # Manter o mais recente
                manter = customers_sorted[0]
                remover = customers_sorted[1:]
                
                self.stdout.write(f'   ✅ Manter: {manter["name"]} (ID: {manter["id"]}) - Criado: {manter.get("dateCreated", "N/A")}')
                
                for customer in remover:
                    self.stdout.write(f'   ❌ Remover: {customer["name"]} (ID: {customer["id"]}) - Criado: {customer.get("dateCreated", "N/A")}')
                    
                    if not dry_run:
                        # Verificar se tem assinatura vinculada
                        tem_assinatura = LojaAssinatura.objects.filter(
                            asaas_customer__asaas_id=customer['id']
                        ).exists()
                        
                        if tem_assinatura:
                            self.stdout.write(self.style.WARNING(f'      ⚠️ Cliente tem assinatura vinculada, pulando'))
                            continue
                        
                        # Verificar se tem cobranças
                        try:
                            payments = client.list_customer_payments(customer['id'])
                            if payments.get('data') and len(payments['data']) > 0:
                                self.stdout.write(self.style.WARNING(f'      ⚠️ Cliente tem cobranças, pulando'))
                                continue
                        except:
                            pass
                        
                        # Remover do Asaas
                        try:
                            client.delete_customer(customer['id'])
                            total_removidos += 1
                            self.stdout.write(self.style.SUCCESS(f'      ✅ Removido do Asaas'))
                            
                            # Remover do banco local se existir
                            AsaasCustomer.objects.filter(asaas_id=customer['id']).delete()
                            
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'      ❌ Erro ao remover: {e}'))
                
                self.stdout.write('')  # Linha em branco
        
        # Resumo
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('✅ Processamento concluído!'))
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f'   Clientes removidos: {total_removidos}'))
        else:
            self.stdout.write(self.style.WARNING('   💡 Execute sem --dry-run para remover os duplicados'))
        
        self.stdout.write(self.style.SUCCESS('='*60))
        
        # Recomendações
        if duplicados_cpf or duplicados_email:
            self.stdout.write(self.style.WARNING('\n💡 Recomendações:'))
            self.stdout.write('   1. Sempre passe customer_id ao criar cobranças')
            self.stdout.write('   2. Use get_or_create ao invés de create')
            self.stdout.write('   3. Verifique externalReference antes de criar')
