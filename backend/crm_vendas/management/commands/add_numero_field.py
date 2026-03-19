"""
Comando para adicionar campo 'numero' nas tabelas de Proposta e Contrato.
Usado quando a migration não foi aplicada corretamente.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Adiciona campo numero nas tabelas crm_vendas_proposta de todas as lojas (se não existir)'

    def handle(self, *args, **options):
        lojas = Loja.objects.filter(is_active=True)
        
        if not lojas.exists():
            self.stdout.write(self.style.WARNING('Nenhuma loja ativa encontrada'))
            return
        
        for loja in lojas:
            self.stdout.write(f'\n📦 Processando loja: {loja.nome} (ID: {loja.id}, Database: {loja.database_name})')
            
            # Conectar ao banco da loja
            db_settings = {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': loja.database_name,
                'USER': connection.settings_dict['USER'],
                'PASSWORD': connection.settings_dict['PASSWORD'],
                'HOST': connection.settings_dict['HOST'],
                'PORT': connection.settings_dict['PORT'],
            }
            
            from django.db import connections
            from django.db.utils import ConnectionHandler
            
            # Criar conexão temporária
            temp_connections = ConnectionHandler({'temp': db_settings})
            temp_conn = temp_connections['temp']
            
            try:
                with temp_conn.cursor() as cursor:
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
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Erro: {str(e)}'))
            finally:
                temp_conn.close()
        
        self.stdout.write(self.style.SUCCESS('\n✅ Comando concluído!'))
