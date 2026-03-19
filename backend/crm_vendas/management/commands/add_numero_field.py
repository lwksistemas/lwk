"""
Comando para adicionar campo 'numero' nas tabelas de Proposta e Contrato.
Usado quando a migration não foi aplicada corretamente.
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Adiciona campo numero nas tabelas crm_vendas_proposta (se não existir)'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Verificar se o campo já existe
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'crm_vendas_proposta' 
                AND column_name = 'numero'
            """)
            
            if cursor.fetchone():
                self.stdout.write(self.style.WARNING('Campo "numero" já existe em crm_vendas_proposta'))
            else:
                # Adicionar o campo
                cursor.execute("""
                    ALTER TABLE crm_vendas_proposta 
                    ADD COLUMN numero VARCHAR(50) DEFAULT '' NOT NULL
                """)
                self.stdout.write(self.style.SUCCESS('✅ Campo "numero" adicionado em crm_vendas_proposta'))
            
            # Remover o DEFAULT após adicionar (para manter compatível com o modelo)
            cursor.execute("""
                ALTER TABLE crm_vendas_proposta 
                ALTER COLUMN numero DROP DEFAULT
            """)
            
        self.stdout.write(self.style.SUCCESS('✅ Comando concluído com sucesso!'))
