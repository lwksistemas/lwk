"""
Comando Django para corrigir números de propostas e contratos existentes.
Gera números sequenciais para propostas e contratos que não têm número ou têm números duplicados.

Uso:
    python manage.py corrigir_numeros
    python manage.py corrigir_numeros --schema=41449198000172
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django_tenants.utils import schema_context, get_tenant_model
from crm_vendas.models import Proposta, Contrato


class Command(BaseCommand):
    help = 'Corrige números de propostas e contratos existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--schema',
            type=str,
            help='Schema específico para processar (slug da loja). Se não fornecido, processa todos.',
        )

    def handle(self, *args, **options):
        schema_especifico = options.get('schema')
        
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("CORREÇÃO DE NÚMEROS DE PROPOSTAS E CONTRATOS"))
        self.stdout.write("=" * 80)
        
        try:
            TenantModel = get_tenant_model()
            
            if schema_especifico:
                # Processar apenas um schema específico
                try:
                    tenant = TenantModel.objects.get(slug=schema_especifico)
                    tenants = [tenant]
                    self.stdout.write(f"\n📍 Processando apenas schema: {schema_especifico}")
                except TenantModel.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"\n❌ Schema '{schema_especifico}' não encontrado!"))
                    return
            else:
                # Processar todos os tenants (exceto public)
                tenants = TenantModel.objects.exclude(schema_name='public')
                self.stdout.write(f"\n📍 Processando {tenants.count()} schemas...")
            
            total_propostas = 0
            total_contratos = 0
            
            for tenant in tenants:
                propostas = self.corrigir_propostas(tenant)
                contratos = self.corrigir_contratos(tenant)
                total_propostas += propostas
                total_contratos += contratos
            
            self.stdout.write("\n" + "=" * 80)
            self.stdout.write(self.style.SUCCESS("✅ CORREÇÃO CONCLUÍDA COM SUCESSO!"))
            self.stdout.write(f"   • Propostas corrigidas: {total_propostas}")
            self.stdout.write(f"   • Contratos corrigidos: {total_contratos}")
            self.stdout.write("=" * 80)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ ERRO: {e}"))
            import traceback
            traceback.print_exc()

    def corrigir_propostas(self, tenant):
        """Corrige números de propostas para um tenant."""
        schema_name = tenant.schema_name
        
        try:
            with schema_context(schema_name):
                self.stdout.write(f"\n📍 Tenant: {schema_name} ({tenant.name})")
                self.stdout.write("   🔧 Corrigindo propostas...")
                
                # Buscar todas as propostas ordenadas por ID (ordem de criação)
                propostas = Proposta.objects.all().order_by('id')
                
                if not propostas.exists():
                    self.stdout.write("      ℹ️  Nenhuma proposta encontrada")
                    return 0
                
                corrigidas = 0
                
                # Renumerar todas as propostas sequencialmente
                for idx, proposta in enumerate(propostas, start=1):
                    numero_novo = str(idx).zfill(3)  # 001, 002, 003...
                    
                    if proposta.numero != numero_novo:
                        numero_antigo = proposta.numero or '(vazio)'
                        proposta.numero = numero_novo
                        proposta.save(update_fields=['numero'])
                        self.stdout.write(f"      ✅ Proposta ID {proposta.id}: {numero_antigo} → {numero_novo}")
                        corrigidas += 1
                    else:
                        self.stdout.write(f"      ✓ Proposta ID {proposta.id}: {proposta.numero} (já correto)")
                
                return corrigidas
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"      ❌ Erro ao processar propostas: {e}"))
            return 0

    def corrigir_contratos(self, tenant):
        """Corrige números de contratos para um tenant."""
        schema_name = tenant.schema_name
        
        try:
            with schema_context(schema_name):
                self.stdout.write("   🔧 Corrigindo contratos...")
                
                # Buscar todos os contratos ordenados por ID (ordem de criação)
                contratos = Contrato.objects.all().order_by('id')
                
                if not contratos.exists():
                    self.stdout.write("      ℹ️  Nenhum contrato encontrado")
                    return 0
                
                corrigidos = 0
                
                # Renumerar todos os contratos sequencialmente
                for idx, contrato in enumerate(contratos, start=1):
                    numero_novo = str(idx).zfill(3)  # 001, 002, 003...
                    
                    if contrato.numero != numero_novo:
                        numero_antigo = contrato.numero or '(vazio)'
                        contrato.numero = numero_novo
                        contrato.save(update_fields=['numero'])
                        self.stdout.write(f"      ✅ Contrato ID {contrato.id}: {numero_antigo} → {numero_novo}")
                        corrigidos += 1
                    else:
                        self.stdout.write(f"      ✓ Contrato ID {contrato.id}: {contrato.numero} (já correto)")
                
                return corrigidos
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"      ❌ Erro ao processar contratos: {e}"))
            return 0
