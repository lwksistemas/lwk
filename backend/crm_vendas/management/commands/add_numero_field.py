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
            schema_name = loja.database_name.replace('-', '_')
            self.stdout.write(f'\n📦 Processando loja: {loja.nome} (ID: {loja.id}, Schema: {schema_name})')
            
            try:
                with connection.cursor() as cursor:
                    # Verificar se o schema existe
                    cursor.execute("""
                        SELECT schema_name 
                        FROM information_schema.schemata 
                        WHERE schema_name = %s
                    """, [schema_name])
                    
                    if not cursor.fetchone():
                        self.stdout.write(self.style.WARNING(f'   Schema não existe'))
                        continue
                    
                    # Setar o search_path para o schema da loja
                    cursor.execute(f'SET search_path TO {schema_name}, public')
                    
                    # Verificar se a tabela existe
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = %s 
                        AND table_name = 'crm_vendas_proposta'
                    """, [schema_name])
                    
                    if not cursor.fetchone():
                        self.stdout.write(self.style.WARNING('   Tabela crm_vendas_proposta não existe'))
                        continue
                    
                    # Verificar se o campo já existe
                    cursor.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_schema = %s
                        AND table_name = 'crm_vendas_proposta' 
                        AND column_name = 'numero'
                    """, [schema_name])
                    
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
        
        self.stdout.write(self.style.SUCCESS('\n✅ Comando concluído!'))
