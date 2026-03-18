from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Cria colunas de assinatura em propostas e contratos'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando criação de colunas de assinatura...\n')
        
        with connection.cursor() as cursor:
            # Verificar e criar colunas em Proposta
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='crm_vendas_proposta' 
                AND column_name IN ('nome_vendedor_assinatura', 'nome_cliente_assinatura');
            """)
            colunas_proposta = [row[0] for row in cursor.fetchall()]
            
            if 'nome_vendedor_assinatura' not in colunas_proposta:
                self.stdout.write('Criando coluna nome_vendedor_assinatura em crm_vendas_proposta...')
                cursor.execute("""
                    ALTER TABLE crm_vendas_proposta 
                    ADD COLUMN nome_vendedor_assinatura VARCHAR(255) NULL;
                """)
                self.stdout.write(self.style.SUCCESS('✅ Coluna nome_vendedor_assinatura criada em crm_vendas_proposta'))
            else:
                self.stdout.write('ℹ️  Coluna nome_vendedor_assinatura já existe em crm_vendas_proposta')
            
            if 'nome_cliente_assinatura' not in colunas_proposta:
                self.stdout.write('Criando coluna nome_cliente_assinatura em crm_vendas_proposta...')
                cursor.execute("""
                    ALTER TABLE crm_vendas_proposta 
                    ADD COLUMN nome_cliente_assinatura VARCHAR(255) NULL;
                """)
                self.stdout.write(self.style.SUCCESS('✅ Coluna nome_cliente_assinatura criada em crm_vendas_proposta'))
            else:
                self.stdout.write('ℹ️  Coluna nome_cliente_assinatura já existe em crm_vendas_proposta')
            
            # Verificar e criar colunas em Contrato
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='crm_vendas_contrato' 
                AND column_name IN ('nome_vendedor_assinatura', 'nome_cliente_assinatura');
            """)
            colunas_contrato = [row[0] for row in cursor.fetchall()]
            
            if 'nome_vendedor_assinatura' not in colunas_contrato:
                self.stdout.write('Criando coluna nome_vendedor_assinatura em crm_vendas_contrato...')
                cursor.execute("""
                    ALTER TABLE crm_vendas_contrato 
                    ADD COLUMN nome_vendedor_assinatura VARCHAR(255) NULL;
                """)
                self.stdout.write(self.style.SUCCESS('✅ Coluna nome_vendedor_assinatura criada em crm_vendas_contrato'))
            else:
                self.stdout.write('ℹ️  Coluna nome_vendedor_assinatura já existe em crm_vendas_contrato')
            
            if 'nome_cliente_assinatura' not in colunas_contrato:
                self.stdout.write('Criando coluna nome_cliente_assinatura em crm_vendas_contrato...')
                cursor.execute("""
                    ALTER TABLE crm_vendas_contrato 
                    ADD COLUMN nome_cliente_assinatura VARCHAR(255) NULL;
                """)
                self.stdout.write(self.style.SUCCESS('✅ Coluna nome_cliente_assinatura criada em crm_vendas_contrato'))
            else:
                self.stdout.write('ℹ️  Coluna nome_cliente_assinatura já existe em crm_vendas_contrato')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Processo concluído!'))
