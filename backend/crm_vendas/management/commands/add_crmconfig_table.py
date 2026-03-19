"""
Comando para adicionar tabela crm_vendas_config em todos os schemas de lojas.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Adiciona tabela crm_vendas_config em todos os schemas de lojas'

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
                    
                    # Verificar se a tabela já existe no schema correto
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = current_schema()
                            AND table_name = 'crm_vendas_config'
                        );
                    """)
                    exists = cursor.fetchone()[0]
                    
                    if exists:
                        self.stdout.write(self.style.WARNING(f'  ⚠️  Tabela já existe no schema {schema_name}'))
                        continue
                    
                    # Criar a tabela no schema correto
                    cursor.execute("""
                        CREATE TABLE crm_vendas_config (
                            id SERIAL PRIMARY KEY,
                            loja_id INTEGER NOT NULL,
                            origens_leads JSONB DEFAULT '[]'::jsonb,
                            etapas_pipeline JSONB DEFAULT '[]'::jsonb,
                            colunas_leads JSONB DEFAULT '[]'::jsonb,
                            modulos_ativos JSONB DEFAULT '{}'::jsonb,
                            proposta_conteudo_padrao TEXT DEFAULT '',
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        );
                        
                        CREATE INDEX crm_config_loja_idx ON crm_vendas_config (loja_id);
                    """)
                    
                    self.stdout.write(self.style.SUCCESS(f'  ✅ Tabela criada com sucesso no schema {schema_name}'))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Erro ao processar schema {schema_name}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Comando concluído!'))
