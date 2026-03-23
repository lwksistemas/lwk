"""
Comando para aplicar migração do campo contato no Lead em todos os schemas de lojas
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Aplica migração do campo contato no Lead em todos os schemas de lojas'

    def handle(self, *args, **options):
        from superadmin.models import Loja
        
        # Listar todas as lojas
        lojas = Loja.objects.filter(is_active=True)
        
        self.stdout.write(self.style.SUCCESS(f'📋 Encontradas {lojas.count()} lojas ativas'))
        self.stdout.write('')
        
        for loja in lojas:
            schema_name = loja.database_name.replace('-', '_')
            
            self.stdout.write(f'🔄 Aplicando migração no schema: {schema_name} (Loja: {loja.nome})')
            
            try:
                with connection.cursor() as cursor:
                    # Verificar se a coluna contato_id já existe
                    cursor.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_schema = %s 
                        AND table_name = 'crm_vendas_lead' 
                        AND column_name = 'contato_id'
                    """, [schema_name])
                    
                    coluna_existe = cursor.fetchone() is not None
                    
                    if coluna_existe:
                        self.stdout.write(self.style.WARNING(f'  ⚠️  Coluna contato_id já existe'))
                    else:
                        # Adicionar coluna contato_id
                        self.stdout.write(f'  ➕ Adicionando coluna contato_id...')
                        cursor.execute(f"""
                            ALTER TABLE {schema_name}.crm_vendas_lead 
                            ADD COLUMN contato_id INTEGER NULL
                        """)
                        
                        # Adicionar foreign key
                        cursor.execute(f"""
                            ALTER TABLE {schema_name}.crm_vendas_lead 
                            ADD CONSTRAINT crm_vendas_lead_contato_id_fkey 
                            FOREIGN KEY (contato_id) 
                            REFERENCES {schema_name}.crm_vendas_contato(id) 
                            ON DELETE SET NULL
                        """)
                        
                        # Criar índice
                        cursor.execute(f"""
                            CREATE INDEX crm_lead_loja_contato_idx 
                            ON {schema_name}.crm_vendas_lead (loja_id, contato_id)
                        """)
                        
                        self.stdout.write(self.style.SUCCESS(f'  ✅ Coluna contato_id adicionada com sucesso'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Erro: {str(e)}'))
                continue
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ Migração aplicada em todos os schemas!'))
