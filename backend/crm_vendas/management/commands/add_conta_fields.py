"""
Comando para adicionar novos campos da tabela Conta em todos os schemas de lojas.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Adiciona novos campos da tabela Conta em todos os schemas de lojas'

    def handle(self, *args, **options):
        lojas = Loja.objects.filter(is_active=True)
        
        self.stdout.write(f'Encontradas {lojas.count()} lojas ativas')
        
        for loja in lojas:
            schema_name = loja.database_name
            self.stdout.write(f'\nProcessando loja {loja.id} - {loja.nome} (schema: {schema_name})')
            
            try:
                with connection.cursor() as cursor:
                    # Setar o search_path para o schema da loja
                    cursor.execute(f"SET search_path TO {schema_name};")
                    
                    # Verificar quais colunas já existem
                    cursor.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_schema = current_schema()
                        AND table_name = 'crm_vendas_conta';
                    """)
                    existing_columns = [row[0] for row in cursor.fetchall()]
                    
                    # Lista de colunas para adicionar
                    columns_to_add = {
                        'razao_social': "VARCHAR(255) DEFAULT ''",
                        'cnpj': "VARCHAR(18) DEFAULT ''",
                        'inscricao_estadual': "VARCHAR(20) DEFAULT ''",
                        'site': "VARCHAR(200)",
                        'cep': "VARCHAR(10) DEFAULT ''",
                        'logradouro': "VARCHAR(255) DEFAULT ''",
                        'numero': "VARCHAR(20) DEFAULT ''",
                        'complemento': "VARCHAR(100) DEFAULT ''",
                        'bairro': "VARCHAR(100) DEFAULT ''",
                        'uf': "VARCHAR(2) DEFAULT ''",
                    }
                    
                    added_count = 0
                    for column_name, column_type in columns_to_add.items():
                        if column_name not in existing_columns:
                            cursor.execute(f"""
                                ALTER TABLE crm_vendas_conta 
                                ADD COLUMN {column_name} {column_type};
                            """)
                            self.stdout.write(self.style.SUCCESS(f'  ✅ Coluna {column_name} adicionada'))
                            added_count += 1
                        else:
                            self.stdout.write(self.style.WARNING(f'  ⚠️  Coluna {column_name} já existe'))
                    
                    if added_count > 0:
                        self.stdout.write(self.style.SUCCESS(f'  ✅ {added_count} colunas adicionadas no schema {schema_name}'))
                    else:
                        self.stdout.write(self.style.SUCCESS(f'  ✅ Todas as colunas já existem no schema {schema_name}'))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Erro ao processar schema {schema_name}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Comando concluído!'))
