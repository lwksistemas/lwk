"""
Management command para verificar dados órfãos no sistema
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import connection
from superadmin.models import Loja, FinanceiroLoja
from asaas_integration.models import AsaasCustomer, LojaAssinatura, AsaasPayment
from mercadopago_integration.models import MercadoPagoCustomer, LojaPagamento

User = get_user_model()


class Command(BaseCommand):
    help = 'Verifica dados órfãos no sistema (schemas, usuários, financeiro, integrações)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar informações detalhadas de cada item',
        )
        parser.add_argument(
            '--show-cleanup-script',
            action='store_true',
            help='Mostrar script de limpeza para dados órfãos encontrados',
        )
    
    def handle(self, *args, **options):
        verbose = options['verbose']
        show_cleanup = options['show_cleanup_script']
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('VERIFICAÇÃO DE DADOS ÓRFÃOS'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
        
        # Coletar todos os órfãos
        all_orphans = {}
        
        # 1. SCHEMAS
        self.stdout.write(self.style.WARNING('1. VERIFICANDO SCHEMAS...'))
        schemas_orfaos = self._check_schemas(verbose)
        all_orphans['schemas'] = schemas_orfaos
        
        # 2. USUÁRIOS
        self.stdout.write(self.style.WARNING('\n2. VERIFICANDO USUÁRIOS...'))
        usuarios_orfaos = self._check_usuarios(verbose)
        all_orphans['usuarios'] = usuarios_orfaos
        
        # 3. FINANCEIRO
        self.stdout.write(self.style.WARNING('\n3. VERIFICANDO FINANCEIRO...'))
        financeiros_orfaos = self._check_financeiro(verbose)
        all_orphans['financeiros'] = financeiros_orfaos
        
        # 4. ASAAS
        self.stdout.write(self.style.WARNING('\n4. VERIFICANDO ASAAS...'))
        asaas_orphans = self._check_asaas(verbose)
        all_orphans.update(asaas_orphans)
        
        # 5. MERCADO PAGO
        self.stdout.write(self.style.WARNING('\n5. VERIFICANDO MERCADO PAGO...'))
        mp_orphans = self._check_mercadopago(verbose)
        all_orphans.update(mp_orphans)
        
        # 6. LOJAS ATIVAS
        self.stdout.write(self.style.WARNING('\n6. LOJAS ATIVAS NO SISTEMA:'))
        self._show_active_lojas()
        
        # RESUMO
        self._show_summary(all_orphans, show_cleanup)
    
    def _check_schemas(self, verbose):
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name NOT IN ('public', 'information_schema', 'pg_catalog', 'pg_toast')
                ORDER BY schema_name;
            """)
            schemas = [row[0] for row in cursor.fetchall()]
        
        self.stdout.write(f'Total de schemas: {len(schemas)}')
        schemas_orfaos = []
        
        for schema in schemas:
            try:
                loja = Loja.objects.get(schema_name=schema)
                if verbose:
                    self.stdout.write(self.style.SUCCESS(f'✅ {schema} → {loja.nome}'))
            except Loja.DoesNotExist:
                schemas_orfaos.append(schema)
                self.stdout.write(self.style.ERROR(f'❌ {schema} → ÓRFÃO'))
        
        return schemas_orfaos
    
    def _check_usuarios(self, verbose):
        usuarios = User.objects.filter(is_superuser=False, is_staff=False)
        self.stdout.write(f'Total de usuários: {usuarios.count()}')
        usuarios_orfaos = []
        
        for usuario in usuarios:
            try:
                loja = Loja.objects.get(usuarios=usuario)
                if verbose:
                    self.stdout.write(self.style.SUCCESS(f'✅ {usuario.username} → {loja.nome}'))
            except Loja.DoesNotExist:
                usuarios_orfaos.append(usuario)
                self.stdout.write(self.style.ERROR(f'❌ {usuario.username} → ÓRFÃO'))
        
        return usuarios_orfaos
    
    def _check_financeiro(self, verbose):
        financeiros = FinanceiroLoja.objects.all()
        self.stdout.write(f'Total de financeiros: {financeiros.count()}')
        financeiros_orfaos = []
        
        for fin in financeiros:
            try:
                loja = Loja.objects.get(financeiro=fin)
                if verbose:
                    self.stdout.write(self.style.SUCCESS(f'✅ Financeiro {fin.id} → {loja.nome}'))
            except Loja.DoesNotExist:
                financeiros_orfaos.append(fin)
                self.stdout.write(self.style.ERROR(f'❌ Financeiro {fin.id} → ÓRFÃO'))
        
        return financeiros_orfaos
    
    def _check_asaas(self, verbose):
        # Customers
        asaas_customers = AsaasCustomer.objects.all()
        self.stdout.write(f'Total de Asaas Customers: {asaas_customers.count()}')
        asaas_customers_orfaos = []
        
        for customer in asaas_customers:
            try:
                loja = Loja.objects.get(slug=customer.loja_slug)
                if verbose:
                    self.stdout.write(self.style.SUCCESS(f'✅ Customer {customer.asaas_id} → {loja.nome}'))
            except Loja.DoesNotExist:
                asaas_customers_orfaos.append(customer)
                self.stdout.write(self.style.ERROR(f'❌ Customer {customer.asaas_id} (slug: {customer.loja_slug}) → ÓRFÃO'))
        
        # Subscriptions
        asaas_subscriptions = LojaAssinatura.objects.all()
        self.stdout.write(f'\nTotal de Asaas Subscriptions: {asaas_subscriptions.count()}')
        asaas_subscriptions_orfaos = []
        
        for sub in asaas_subscriptions:
            if sub.customer in asaas_customers_orfaos:
                asaas_subscriptions_orfaos.append(sub)
                if verbose:
                    self.stdout.write(self.style.ERROR(f'❌ Subscription {sub.asaas_id} → Customer órfão'))
            else:
                try:
                    loja = Loja.objects.get(slug=sub.customer.loja_slug)
                    if verbose:
                        self.stdout.write(self.style.SUCCESS(f'✅ Subscription {sub.asaas_id} → {loja.nome}'))
                except Loja.DoesNotExist:
                    asaas_subscriptions_orfaos.append(sub)
                    self.stdout.write(self.style.ERROR(f'❌ Subscription {sub.asaas_id} → ÓRFÃO'))
        
        # Payments
        asaas_payments = AsaasPayment.objects.all()
        self.stdout.write(f'\nTotal de Asaas Payments: {asaas_payments.count()}')
        asaas_payments_orfaos = []
        
        for payment in asaas_payments:
            if payment.customer in asaas_customers_orfaos:
                asaas_payments_orfaos.append(payment)
                if verbose:
                    self.stdout.write(self.style.ERROR(f'❌ Payment {payment.asaas_id} → Customer órfão'))
            else:
                try:
                    loja = Loja.objects.get(slug=payment.customer.loja_slug)
                    if verbose:
                        self.stdout.write(self.style.SUCCESS(f'✅ Payment {payment.asaas_id} → {loja.nome}'))
                except Loja.DoesNotExist:
                    asaas_payments_orfaos.append(payment)
                    self.stdout.write(self.style.ERROR(f'❌ Payment {payment.asaas_id} → ÓRFÃO'))
        
        return {
            'asaas_customers': asaas_customers_orfaos,
            'asaas_subscriptions': asaas_subscriptions_orfaos,
            'asaas_payments': asaas_payments_orfaos,
        }
    
    def _check_mercadopago(self, verbose):
        # Customers
        mp_customers = MercadoPagoCustomer.objects.all()
        self.stdout.write(f'Total de MP Customers: {mp_customers.count()}')
        mp_customers_orfaos = []
        
        for customer in mp_customers:
            try:
                loja = Loja.objects.get(slug=customer.loja_slug)
                if verbose:
                    self.stdout.write(self.style.SUCCESS(f'✅ Customer {customer.mercadopago_id} → {loja.nome}'))
            except Loja.DoesNotExist:
                mp_customers_orfaos.append(customer)
                self.stdout.write(self.style.ERROR(f'❌ Customer {customer.mercadopago_id} (slug: {customer.loja_slug}) → ÓRFÃO'))
        
        # Pagamentos
        mp_pagamentos = LojaPagamento.objects.all()
        self.stdout.write(f'\nTotal de MP Pagamentos: {mp_pagamentos.count()}')
        mp_pagamentos_orfaos = []
        
        for pag in mp_pagamentos:
            try:
                loja = Loja.objects.get(slug=pag.loja_slug)
                if verbose:
                    self.stdout.write(self.style.SUCCESS(f'✅ Pagamento {pag.mercadopago_payment_id} → {loja.nome}'))
            except Loja.DoesNotExist:
                mp_pagamentos_orfaos.append(pag)
                self.stdout.write(self.style.ERROR(f'❌ Pagamento {pag.mercadopago_payment_id} (slug: {pag.loja_slug}) → ÓRFÃO'))
        
        return {
            'mp_customers': mp_customers_orfaos,
            'mp_pagamentos': mp_pagamentos_orfaos,
        }
    
    def _show_active_lojas(self):
        lojas = Loja.objects.all().order_by('nome')
        self.stdout.write(f'Total: {lojas.count()}')
        for loja in lojas:
            self.stdout.write(f'  🏪 {loja.nome} (slug: {loja.slug}, schema: {loja.schema_name})')
    
    def _show_summary(self, all_orphans, show_cleanup):
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('RESUMO'))
        self.stdout.write(self.style.SUCCESS('='*80))
        
        counts = {
            'Schemas órfãos': len(all_orphans.get('schemas', [])),
            'Usuários órfãos': len(all_orphans.get('usuarios', [])),
            'Financeiro órfão': len(all_orphans.get('financeiros', [])),
            'Asaas Customers órfãos': len(all_orphans.get('asaas_customers', [])),
            'Asaas Subscriptions órfãos': len(all_orphans.get('asaas_subscriptions', [])),
            'Asaas Payments órfãos': len(all_orphans.get('asaas_payments', [])),
            'MP Customers órfãos': len(all_orphans.get('mp_customers', [])),
            'MP Pagamentos órfãos': len(all_orphans.get('mp_pagamentos', [])),
        }
        
        for label, count in counts.items():
            self.stdout.write(f'{label}: {count}')
        
        total_orfaos = sum(counts.values())
        self.stdout.write(f'\nTOTAL DE ÓRFÃOS: {total_orfaos}')
        
        if total_orfaos == 0:
            self.stdout.write(self.style.SUCCESS('\n✅ SISTEMA LIMPO! Nenhum dado órfão encontrado.'))
        elif show_cleanup:
            self._show_cleanup_script(all_orphans)
        else:
            self.stdout.write(self.style.WARNING('\n⚠️  Use --show-cleanup-script para ver comandos de limpeza'))
        
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
    
    def _show_cleanup_script(self, all_orphans):
        self.stdout.write(self.style.WARNING('\n⚠️  COMANDOS DE LIMPEZA:'))
        self.stdout.write('='*80)
        
        if all_orphans.get('schemas'):
            self.stdout.write('\n# Schemas (SQL):')
            for schema in all_orphans['schemas']:
                self.stdout.write(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE;')
        
        # Para usar o comando de limpeza automatizado
        self.stdout.write('\n# Ou use o comando automatizado:')
        self.stdout.write('python manage.py cleanup_orfaos --dry-run')
        self.stdout.write('python manage.py cleanup_orfaos  # Para executar de fato')
