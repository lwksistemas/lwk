"""
Comando Django para corrigir números de propostas e contratos existentes.
Gera números sequenciais para propostas e contratos que não têm número ou têm números duplicados.

Uso:
    python manage.py corrigir_numeros --schema=41449198000172
"""
from django.core.management.base import BaseCommand
from django.db import connection


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
            total_propostas = self.corrigir_propostas(schema_name)
            total_contratos = self.corrigir_contratos(schema_name)
            
            self.stdout.write("\n" + "=" * 80)
            self.stdout.write(self.style.SUCCESS("✅ CORREÇÃO CONCLUÍDA COM SUCESSO!"))
            self.stdout.write(f"   • Propostas corrigidas: {total_propostas}")
            self.stdout.write(f"   • Contratos corrigidos: {total_contratos}")
            self.stdout.write("=" * 80)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ ERRO: {e}"))
            import traceback
            traceback.print_exc()

    def corrigir_propostas(self, schema_name):
        """Corrige números de propostas usando SQL direto."""
        
        try:
            self.stdout.write(f"\n   🔧 Corrigindo propostas...")
            
            with connection.cursor() as cursor:
                # Mudar para o schema
                cursor.execute(f'SET search_path TO "{schema_name}"')
                
                # Buscar todas as propostas ordenadas por ID
                cursor.execute("""
                    SELECT id, numero
                    FROM crm_vendas_proposta
                    ORDER BY id
                """)
                
                propostas = cursor.fetchall()
                
                if not propostas:
                    self.stdout.write("      ℹ️  Nenhuma proposta encontrada")
                    return 0
                
                corrigidas = 0
                
                # Renumerar todas as propostas sequencialmente
                for idx, (proposta_id, numero_atual) in enumerate(propostas, start=1):
                    numero_novo = str(idx).zfill(3)  # 001, 002, 003...
                    
                    if numero_atual != numero_novo:
                        numero_antigo = numero_atual or '(vazio)'
                        
                        # Atualizar o número
                        cursor.execute("""
                            UPDATE crm_vendas_proposta
                            SET numero = %s
                            WHERE id = %s
                        """, [numero_novo, proposta_id])
                        
                        self.stdout.write(f"      ✅ Proposta ID {proposta_id}: {numero_antigo} → {numero_novo}")
                        corrigidas += 1
                    else:
                        self.stdout.write(f"      ✓ Proposta ID {proposta_id}: {numero_atual} (já correto)")
                
                # Voltar para o schema public
                cursor.execute('SET search_path TO public')
                
                return corrigidas
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"      ❌ Erro ao processar propostas: {e}"))
            import traceback
            traceback.print_exc()
            return 0

    def corrigir_contratos(self, schema_name):
        """Corrige números de contratos usando SQL direto."""
        
        try:
            self.stdout.write("   🔧 Corrigindo contratos...")
            
            with connection.cursor() as cursor:
                # Mudar para o schema
                cursor.execute(f'SET search_path TO "{schema_name}"')
                
                # Buscar todos os contratos ordenados por ID
                cursor.execute("""
                    SELECT id, numero
                    FROM crm_vendas_contrato
                    ORDER BY id
                """)
                
                contratos = cursor.fetchall()
                
                if not contratos:
                    self.stdout.write("      ℹ️  Nenhum contrato encontrado")
                    return 0
                
                corrigidos = 0
                
                # Renumerar todos os contratos sequencialmente
                for idx, (contrato_id, numero_atual) in enumerate(contratos, start=1):
                    numero_novo = str(idx).zfill(3)  # 001, 002, 003...
                    
                    if numero_atual != numero_novo:
                        numero_antigo = numero_atual or '(vazio)'
                        
                        # Atualizar o número
                        cursor.execute("""
                            UPDATE crm_vendas_contrato
                            SET numero = %s
                            WHERE id = %s
                        """, [numero_novo, contrato_id])
                        
                        self.stdout.write(f"      ✅ Contrato ID {contrato_id}: {numero_antigo} → {numero_novo}")
                        corrigidos += 1
                    else:
                        self.stdout.write(f"      ✓ Contrato ID {contrato_id}: {numero_atual} (já correto)")
                
                # Voltar para o schema public
                cursor.execute('SET search_path TO public')
                
                return corrigidos
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"      ❌ Erro ao processar contratos: {e}"))
            import traceback
            traceback.print_exc()
            return 0
