"""
Comando para corrigir schema CRM de lojas existentes.
Aplica migrations e cria tabelas faltantes.

Uso:
    python manage.py corrigir_schema_crm
    python manage.py corrigir_schema_crm --loja-id=123
"""
from django.core.management.base import BaseCommand
from django.db import connection
from superadmin.models import Loja
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Corrige schema CRM de lojas existentes (aplica migrations e cria tabelas)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loja-id',
            type=int,
            help='ID da loja específica para corrigir (opcional)',
        )

    def handle(self, *args, **options):
        loja_id = options.get('loja_id')
        
        # Filtrar lojas CRM Vendas
        lojas_qs = Loja.objects.using('default').select_related('tipo_loja')
        if loja_id:
            lojas_qs = lojas_qs.filter(id=loja_id)
        else:
            lojas_qs = lojas_qs.filter(tipo_loja__nome='CRM Vendas')
        
        lojas = list(lojas_qs)
        
        if not lojas:
            self.stdout.write(self.style.WARNING('Nenhuma loja CRM Vendas encontrada'))
            return
        
        self.stdout.write(f'Encontradas {len(lojas)} loja(s) CRM Vendas')
        
        for loja in lojas:
            self.stdout.write(f'\n📦 Processando loja: {loja.nome} (ID: {loja.id})')
            
            try:
                # 1. Configurar schema e aplicar migrations
                from crm_vendas.schema_service import configurar_schema_crm_loja
                if not configurar_schema_crm_loja(loja):
                    self.stdout.write(self.style.ERROR(f'  ❌ Falha ao configurar schema'))
                    continue
                
                self.stdout.write(self.style.SUCCESS(f'  ✅ Schema configurado'))
                
                # 2. Criar tabelas de produtos/itens se não existirem
                db_name = loja.database_name
                schema_name = db_name.replace('-', '_')
                
                with connection.cursor() as cursor:
                    cursor.execute(f'SET search_path TO "{schema_name}", public;')
                    
                    # Verificar se tabela oportunidade_item existe
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = %s
                            AND table_name = 'crm_vendas_oportunidade_item'
                        );
                    """, [schema_name])
                    
                    existe = cursor.fetchone()[0]
                    
                    if not existe:
                        self.stdout.write('  📝 Criando tabelas de produtos/itens...')
                        self._criar_tabelas_crm(cursor, schema_name)
                        self.stdout.write(self.style.SUCCESS(f'  ✅ Tabelas criadas'))
                    else:
                        self.stdout.write('  ℹ️  Tabelas já existem')
                
                self.stdout.write(self.style.SUCCESS(f'✅ Loja {loja.nome} corrigida com sucesso'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Erro: {e}'))
                logger.exception(f'Erro ao corrigir loja {loja.id}')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Processamento concluído'))

    def _criar_tabelas_crm(self, cursor, schema_name):
        """Cria tabelas de ProdutoServico, OportunidadeItem, Proposta e Contrato."""
        
        # Criar tabela ProdutoServico
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS "{schema_name}".crm_vendas_produto_servico (
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
            ON "{schema_name}".crm_vendas_produto_servico (loja_id, tipo);
        """)
        
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS crm_ps_loja_ativo_idx 
            ON "{schema_name}".crm_vendas_produto_servico (loja_id, ativo);
        """)
        
        # Criar tabela OportunidadeItem
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS "{schema_name}".crm_vendas_oportunidade_item (
                id BIGSERIAL PRIMARY KEY,
                loja_id INTEGER NOT NULL,
                oportunidade_id BIGINT NOT NULL REFERENCES "{schema_name}".crm_vendas_oportunidade(id) ON DELETE CASCADE,
                produto_servico_id BIGINT NOT NULL REFERENCES "{schema_name}".crm_vendas_produto_servico(id) ON DELETE CASCADE,
                quantidade DECIMAL(10, 2) NOT NULL DEFAULT 1,
                preco_unitario DECIMAL(12, 2) NOT NULL,
                observacao VARCHAR(255),
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
        """)
        
        # Criar índice para OportunidadeItem
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS crm_oi_loja_opor_idx 
            ON "{schema_name}".crm_vendas_oportunidade_item (loja_id, oportunidade_id);
        """)
        
        # Criar tabela Proposta
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS "{schema_name}".crm_vendas_proposta (
                id BIGSERIAL PRIMARY KEY,
                loja_id INTEGER NOT NULL,
                oportunidade_id BIGINT NOT NULL REFERENCES "{schema_name}".crm_vendas_oportunidade(id) ON DELETE CASCADE,
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
            ON "{schema_name}".crm_vendas_proposta (loja_id, oportunidade_id);
        """)
        
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS crm_prop_loja_status_idx 
            ON "{schema_name}".crm_vendas_proposta (loja_id, status);
        """)
        
        # Criar tabela Contrato
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS "{schema_name}".crm_vendas_contrato (
                id BIGSERIAL PRIMARY KEY,
                loja_id INTEGER NOT NULL,
                oportunidade_id BIGINT NOT NULL UNIQUE REFERENCES "{schema_name}".crm_vendas_oportunidade(id) ON DELETE CASCADE,
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
            ON "{schema_name}".crm_vendas_contrato (loja_id, oportunidade_id);
        """)
        
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS crm_cont_loja_status_idx 
            ON "{schema_name}".crm_vendas_contrato (loja_id, status);
        """)
