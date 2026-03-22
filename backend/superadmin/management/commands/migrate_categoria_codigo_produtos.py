"""
Comando para adicionar campos categoria e codigo nas tabelas de produtos/serviços
dos schemas isolados das lojas CRM Vendas.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Adiciona campos categoria e codigo nas tabelas de produtos/serviços dos schemas das lojas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--slug',
            type=str,
            help='Slug da loja específica (opcional, se não informado processa todas)',
        )

    def handle(self, *args, **options):
        slug = options.get('slug')
        
        if slug:
            lojas = Loja.objects.filter(slug=slug, tipo_loja__nome='CRM Vendas')
        else:
            lojas = Loja.objects.filter(tipo_loja__nome='CRM Vendas')
        
        total = lojas.count()
        self.stdout.write(f'Processando {total} loja(s) CRM Vendas...\n')
        
        for loja in lojas:
            self.processar_loja(loja)
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Processamento concluído! {total} loja(s) processada(s)'))

    def processar_loja(self, loja):
        schema_name = f'loja_{loja.slug}'
        self.stdout.write(f'\n📦 Loja: {loja.nome} (schema: {schema_name})')
        
        with connection.cursor() as cursor:
            # Verificar se o schema existe
            cursor.execute(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                [schema_name]
            )
            if not cursor.fetchone():
                self.stdout.write(self.style.WARNING(f'   ⚠️  Schema {schema_name} não existe'))
                return
            
            # Mudar para o schema da loja
            cursor.execute(f'SET search_path TO {schema_name}')
            
            # 1. Criar tabela de categorias
            self.stdout.write('   Criando tabela crm_vendas_categoria_produto_servico...')
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS "{schema_name}".crm_vendas_categoria_produto_servico (
                    id BIGSERIAL PRIMARY KEY,
                    loja_id INTEGER NOT NULL,
                    nome VARCHAR(100) NOT NULL,
                    descricao TEXT,
                    cor VARCHAR(7) NOT NULL DEFAULT '#3B82F6',
                    ordem INTEGER NOT NULL DEFAULT 0,
                    ativo BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                );
            """)
            self.stdout.write(self.style.SUCCESS('   ✅ Tabela de categorias criada'))
            
            # Criar índices para categorias
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS crm_cat_ps_loja_ativo_idx 
                ON "{schema_name}".crm_vendas_categoria_produto_servico (loja_id, ativo);
            """)
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS crm_cat_ps_loja_ordem_idx 
                ON "{schema_name}".crm_vendas_categoria_produto_servico (loja_id, ordem);
            """)
            
            # 2. Verificar se a tabela de produtos/serviços existe
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = '{schema_name}' 
                    AND table_name = 'crm_vendas_produto_servico'
                );
            """)
            tabela_existe = cursor.fetchone()[0]
            
            if not tabela_existe:
                self.stdout.write(self.style.WARNING('   ⚠️  Tabela crm_vendas_produto_servico não existe'))
                return
            
            # 3. Adicionar campo codigo se não existir
            cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = '{schema_name}' 
                AND table_name = 'crm_vendas_produto_servico' 
                AND column_name = 'codigo';
            """)
            
            if not cursor.fetchone():
                self.stdout.write('   Adicionando campo codigo...')
                cursor.execute(f"""
                    ALTER TABLE "{schema_name}".crm_vendas_produto_servico 
                    ADD COLUMN codigo VARCHAR(50);
                """)
                self.stdout.write(self.style.SUCCESS('   ✅ Campo codigo adicionado'))
            else:
                self.stdout.write('   ℹ️  Campo codigo já existe')
            
            # 4. Adicionar campo categoria_id se não existir
            cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = '{schema_name}' 
                AND table_name = 'crm_vendas_produto_servico' 
                AND column_name = 'categoria_id';
            """)
            
            if not cursor.fetchone():
                self.stdout.write('   Adicionando campo categoria_id...')
                cursor.execute(f"""
                    ALTER TABLE "{schema_name}".crm_vendas_produto_servico 
                    ADD COLUMN categoria_id BIGINT REFERENCES "{schema_name}".crm_vendas_categoria_produto_servico(id) ON DELETE SET NULL;
                """)
                self.stdout.write(self.style.SUCCESS('   ✅ Campo categoria_id adicionado'))
            else:
                self.stdout.write('   ℹ️  Campo categoria_id já existe')
            
            # 5. Criar índices para os novos campos
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS crm_ps_loja_cat_idx 
                ON "{schema_name}".crm_vendas_produto_servico (loja_id, categoria_id);
            """)
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS crm_ps_loja_codigo_idx 
                ON "{schema_name}".crm_vendas_produto_servico (loja_id, codigo);
            """)
            
            # 6. Criar constraint de unicidade para código (se não existir)
            cursor.execute(f"""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_schema = '{schema_name}' 
                AND table_name = 'crm_vendas_produto_servico' 
                AND constraint_name = 'crm_ps_unique_codigo_loja';
            """)
            
            if not cursor.fetchone():
                self.stdout.write('   Criando constraint de unicidade para codigo...')
                cursor.execute(f"""
                    ALTER TABLE "{schema_name}".crm_vendas_produto_servico 
                    ADD CONSTRAINT crm_ps_unique_codigo_loja 
                    UNIQUE (loja_id, codigo) 
                    WHERE codigo IS NOT NULL AND codigo != '';
                """)
                self.stdout.write(self.style.SUCCESS('   ✅ Constraint criada'))
            else:
                self.stdout.write('   ℹ️  Constraint já existe')
            
            # Voltar ao schema public
            cursor.execute('SET search_path TO public')
            
            self.stdout.write(self.style.SUCCESS(f'   ✅ Loja {loja.nome} processada com sucesso!'))
