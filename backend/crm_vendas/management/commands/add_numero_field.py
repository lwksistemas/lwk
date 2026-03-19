"""
Comando para adicionar campo 'numero' nas tabelas de Proposta e Contrato.
Usado quando a migration não foi aplicada corretamente.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from superadmin.models import Loja
import psycopg2


class Command(BaseCommand):
    help = 'Adiciona campo numero nas tabelas crm_vendas_proposta de todas as lojas (se não existir)'

    def handle(self, *args, **options):
        lojas = Loja.objects.filter(is_active=True)
        
        if not lojas.exists():
            self.stdout.write(self.style.WARNING('Nenhuma loja ativa encontrada'))
            return
        
        # Pegar credenciais do banco
        db_config = connection.settings_dict
        
        for loja in lojas:
            self.stdout.write(f'\n📦 Processando loja: {loja.nome} (ID: {loja.id}, Database: {loja.database_name})')
            
            try:
                # Conectar diretamente ao banco da loja
                conn = psycopg2.connect(
                    dbname=loja.database_name,
                    user=db_config['USER'],
                    password=db_config['PASSWORD'],
                    host=db_config['HOST'],
                    port=db_config['PORT']
                )
                conn.autocommit = True
                cursor = conn.cursor()
                
                # Verificar se o campo já existe
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'crm_vendas_proposta' 
                    AND column_name = 'numero'
                """)
                
                if cursor.fetchone():
                    self.stdout.write(self.style.WARNING('   Campo "numero" já existe'))
                else:
                    # Adicionar o campo
                    cursor.execute("""
                        ALTER TABLE crm_vendas_proposta 
                        ADD COLUMN numero VARCHAR(50) DEFAULT '' NOT NULL
                    """)
                    
                    # Remover o DEFAULT após adicionar
                    cursor.execute("""
                        ALTER TABLE crm_vendas_proposta 
                        ALTER COLUMN numero DROP DEFAULT
                    """)
                    
                    self.stdout.write(self.style.SUCCESS('   ✅ Campo "numero" adicionado'))
                
                cursor.close()
                conn.close()
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Erro: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Comando concluído!'))
