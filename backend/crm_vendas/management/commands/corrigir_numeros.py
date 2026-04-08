"""
Comando Django para corrigir números de propostas e contratos existentes.
Gera números sequenciais para propostas e contratos que não têm número ou têm números duplicados.

Uso:
    python manage.py corrigir_numeros --schema=41449198000172
"""
from django.core.management.base import BaseCommand
from django.db import connection
from crm_vendas.models import Proposta, Contrato


class Command(BaseCommand):
    help = 'Corrige números de propostas e contratos existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--schema',
            type=str,
            required=True,
            help='Schema específico para processar (slug da loja).',
        )

    def handle(self, *args, **options):
        schema_name = options.get('schema')
        
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("CORREÇÃO DE NÚMEROS DE PROPOSTAS E CONTRATOS"))
        self.stdout.write("=" * 80)
        self.stdout.write(f"\n📍 Processando schema: {schema_name}")
        
        try:
            # Mudar para o schema específico
            with connection.cursor() as cursor:
                cursor.execute(f'SET search_path TO "{schema_name}"')
            
            total_propostas = self.corrigir_propostas()
            total_contratos = self.corrigir_contratos()
            
            # Voltar para o schema public
            with connection.cursor() as cursor:
                cursor.execute('SET search_path TO public')
            
            self.stdout.write("\n" + "=" * 80)
            self.stdout.write(self.style.SUCCESS("✅ CORREÇÃO CONCLUÍDA COM SUCESSO!"))
            self.stdout.write(f"   • Propostas corrigidas: {total_propostas}")
            self.stdout.write(f"   • Contratos corrigidos: {total_contratos}")
            self.stdout.write("=" * 80)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ ERRO: {e}"))
            import traceback
            traceback.print_exc()

    def corrigir_propostas(self):
        """Corrige números de propostas."""
        
        try:
            self.stdout.write(f"\n   🔧 Corrigindo propostas...")
            
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

    def corrigir_contratos(self):
        """Corrige números de contratos."""
        
        try:
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
