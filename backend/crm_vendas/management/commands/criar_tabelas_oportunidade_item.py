"""
Comando para criar tabelas de OportunidadeItem, ProdutoServico, Proposta e Contrato.
Uso: python manage.py criar_tabelas_oportunidade_item
"""
from django.core.management.base import BaseCommand
from django.db import connection
from tenants.utils import get_tenant_database_alias
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Cria tabelas de OportunidadeItem, ProdutoServico, Proposta e Contrato em todas as lojas'

    def handle(self, *args, **options):
        self.stdout.write('🔧 Criando tabelas de produtos e itens...')
        
        lojas = Loja.objects.using('default').filter(is_active=True)
        total = lojas.count()
        sucesso = 0
        erros = 0
        
        for loja in lojas:
            try:
                db_alias = get_tenant_database_alias(loja)
                
                with connection.cursor() as cursor:
                    cursor.execute(f"SET search_path TO {loja.database_name}, public;")
                    
                    # Verificar se tabela já existe
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = %s
                            AND table_name = 'crm_vendas_oportunidade_item'
                        );
                    """, [loja.database_name])
                    
                    existe = cursor.fetchone()[0]
                    
                    if existe:
                        self.stdout.write(f'  ⏭️  Loja {loja.slug}: tabelas já existem')
                        sucesso += 1
                        continue
                    
                    # Criar tabela ProdutoServico
                    cursor.execute(f"""
                        CREATE TABLE IF NOT EXISTS {loja.database_name}.crm_vendas_produto_servico (
                            id BIGSERIAL PRIMARY KEY,
                            loja_id INTEGER NOT NULL,
                            tipo VARCHAR(20) NOT NULL DEFAULT 'produto',
                            nome VARCHAR(255) NOT NULL,
                            descricao TEXT,
                            preco DECIMAL(12, 2) NOT NULL DEFAULT 0,
                            ativo BOOLEAN NOT NULL DEFAULT TRUE,
                            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                        );
                    """)
                    
                    # Criar índices para ProdutoServico
                    cursor.execute(f"""
                        CREATE INDEX IF NOT EXISTS crm_ps_loja_tipo_idx 
                        ON {loja.database_name}.crm_vendas_produto_servico (loja_id, tipo);
                    """)
                    
                    cursor.execute(f"""
                        CREATE INDEX IF NOT EXISTS crm_ps_loja_ativo_idx 
                        ON {loja.database_name}.crm_vendas_produto_servico (loja_id, ativo);
                    """)
                    
                    # Criar tabela OportunidadeItem
                    cursor.execute(f"""
                        CREATE TABLE IF NOT EXISTS {loja.database_name}.crm_vendas_oportunidade_item (
                            id BIGSERIAL PRIMARY KEY,
                            loja_id INTEGER NOT NULL,
                            oportunidade_id BIGINT NOT NULL REFERENCES {loja.database_name}.crm_vendas_oportunidade(id) ON DELETE CASCADE,
                            produto_servico_id BIGINT NOT NULL REFERENCES {loja.database_name}.crm_vendas_produto_servico(id) ON DELETE CASCADE,
                            quantidade DECIMAL(10, 2) NOT NULL DEFAULT 1,
                            preco_unitario DECIMAL(12, 2) NOT NULL,
                            observacao VARCHAR(255),
                            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                        );
                    """)
                    
                    # Criar índice para OportunidadeItem
                    cursor.execute(f"""
                        CREATE INDEX IF NOT EXISTS crm_oi_loja_opor_idx 
                        ON {loja.database_name}.crm_vendas_oportunidade_item (loja_id, oportunidade_id);
                    """)
                    
                    # Criar tabela Proposta
                    cursor.execute(f"""
                        CREATE TABLE IF NOT EXISTS {loja.database_name}.crm_vendas_proposta (
                            id BIGSERIAL PRIMARY KEY,
                            loja_id INTEGER NOT NULL,
                            oportunidade_id BIGINT NOT NULL REFERENCES {loja.database_name}.crm_vendas_oportunidade(id) ON DELETE CASCADE,
                            titulo VARCHAR(255) NOT NULL,
                            conteudo TEXT,
                            valor_total DECIMAL(12, 2),
                            status VARCHAR(20) NOT NULL DEFAULT 'rascunho',
                            data_envio TIMESTAMP WITH TIME ZONE,
                            data_resposta TIMESTAMP WITH TIME ZONE,
                            observacoes TEXT,
                            nome_vendedor_assinatura VARCHAR(255),
                            nome_cliente_assinatura VARCHAR(255),
                            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                        );
                    """)
                    
                    # Criar índices para Proposta
                    cursor.execute(f"""
                        CREATE INDEX IF NOT EXISTS crm_prop_loja_opor_idx 
                        ON {loja.database_name}.crm_vendas_proposta (loja_id, oportunidade_id);
                    """)
                    
                    cursor.execute(f"""
                        CREATE INDEX IF NOT EXISTS crm_prop_loja_status_idx 
                        ON {loja.database_name}.crm_vendas_proposta (loja_id, status);
                    """)
                    
                    # Criar tabela Contrato
                    cursor.execute(f"""
                        CREATE TABLE IF NOT EXISTS {loja.database_name}.crm_vendas_contrato (
                            id BIGSERIAL PRIMARY KEY,
                            loja_id INTEGER NOT NULL,
                            oportunidade_id BIGINT NOT NULL UNIQUE REFERENCES {loja.database_name}.crm_vendas_oportunidade(id) ON DELETE CASCADE,
                            numero VARCHAR(50),
                            titulo VARCHAR(255) NOT NULL,
                            conteudo TEXT,
                            valor_total DECIMAL(12, 2),
                            status VARCHAR(20) NOT NULL DEFAULT 'rascunho',
                            data_envio TIMESTAMP WITH TIME ZONE,
                            data_assinatura TIMESTAMP WITH TIME ZONE,
                            observacoes TEXT,
                            nome_vendedor_assinatura VARCHAR(255),
                            nome_cliente_assinatura VARCHAR(255),
                            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                        );
                    """)
                    
                    # Criar índices para Contrato
                    cursor.execute(f"""
                        CREATE INDEX IF NOT EXISTS crm_cont_loja_opor_idx 
                        ON {loja.database_name}.crm_vendas_contrato (loja_id, oportunidade_id);
                    """)
                    
                    cursor.execute(f"""
                        CREATE INDEX IF NOT EXISTS crm_cont_loja_status_idx 
                        ON {loja.database_name}.crm_vendas_contrato (loja_id, status);
                    """)
                    
                    self.stdout.write(self.style.SUCCESS(f'  ✅ Loja {loja.slug}: tabelas criadas'))
                    sucesso += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Loja {loja.slug}: {e}'))
                erros += 1
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'✅ Concluído: {sucesso}/{total} lojas'))
        if erros > 0:
            self.stdout.write(self.style.WARNING(f'⚠️  {erros} erros'))
