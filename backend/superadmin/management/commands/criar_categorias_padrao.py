"""
Comando para criar categorias padrão de produtos/serviços para lojas CRM Vendas.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Cria categorias padrão de produtos/serviços para lojas CRM Vendas'

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
        
        # Categorias padrão com cores
        categorias = [
            {'nome': 'Hardware', 'descricao': 'Equipamentos e componentes físicos', 'cor': '#3B82F6', 'ordem': 1},
            {'nome': 'Software', 'descricao': 'Licenças e sistemas', 'cor': '#8B5CF6', 'ordem': 2},
            {'nome': 'Consultoria', 'descricao': 'Serviços de consultoria especializada', 'cor': '#10B981', 'ordem': 3},
            {'nome': 'Suporte Técnico', 'descricao': 'Serviços de suporte e manutenção', 'cor': '#F59E0B', 'ordem': 4},
            {'nome': 'Treinamento', 'descricao': 'Cursos e capacitação', 'cor': '#EF4444', 'ordem': 5},
        ]
        
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
            
            # Verificar se a tabela de categorias existe
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = '{schema_name}' 
                    AND table_name = 'crm_vendas_categoria_produto_servico'
                );
            """)
            tabela_existe = cursor.fetchone()[0]
            
            if not tabela_existe:
                self.stdout.write(self.style.WARNING('   ⚠️  Tabela de categorias não existe. Execute migrate_categoria_codigo_produtos primeiro.'))
                return
            
            # Criar categorias
            categorias_criadas = 0
            categorias_existentes = 0
            
            for cat in categorias:
                # Verificar se já existe
                cursor.execute(
                    f'SELECT id FROM "{schema_name}".crm_vendas_categoria_produto_servico WHERE nome = %s AND loja_id = %s',
                    [cat['nome'], loja.id]
                )
                
                if cursor.fetchone():
                    categorias_existentes += 1
                    self.stdout.write(f'   ℹ️  Categoria "{cat["nome"]}" já existe')
                else:
                    # Criar categoria
                    cursor.execute(f"""
                        INSERT INTO "{schema_name}".crm_vendas_categoria_produto_servico 
                        (loja_id, nome, descricao, cor, ordem, ativo, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                    """, [loja.id, cat['nome'], cat['descricao'], cat['cor'], cat['ordem'], True])
                    categorias_criadas += 1
                    self.stdout.write(self.style.SUCCESS(f'   ✅ Categoria "{cat["nome"]}" criada'))
            
            # Voltar ao schema public
            cursor.execute('SET search_path TO public')
            
            if categorias_criadas > 0:
                self.stdout.write(self.style.SUCCESS(f'   ✅ {categorias_criadas} categoria(s) criada(s)'))
            if categorias_existentes > 0:
                self.stdout.write(f'   ℹ️  {categorias_existentes} categoria(s) já existia(m)')
