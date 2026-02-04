"""
Comando para executar migrações do app cabeleireiro em todas as lojas de cabeleireiro.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from stores.models import Loja


class Command(BaseCommand):
    help = 'Executa migrações do app cabeleireiro em todas as lojas de cabeleireiro'

    def handle(self, *args, **options):
        # Buscar todas as lojas de cabeleireiro
        lojas_cabeleireiro = Loja.objects.filter(tipo_loja__nome__icontains='cabeleireiro')
        
        self.stdout.write(f'Encontradas {lojas_cabeleireiro.count()} lojas de cabeleireiro')
        
        for loja in lojas_cabeleireiro:
            self.stdout.write(f'\n📍 Processando loja: {loja.nome} (ID: {loja.id}, Slug: {loja.slug})')
            
            try:
                # Conectar ao schema da loja
                schema_name = f'loja_{loja.slug.replace("-", "_")}'
                
                with connection.cursor() as cursor:
                    # Verificar se o schema existe
                    cursor.execute(
                        "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                        [schema_name]
                    )
                    if not cursor.fetchone():
                        self.stdout.write(self.style.WARNING(f'  ⚠️  Schema {schema_name} não existe'))
                        continue
                    
                    # Setar o search_path para o schema da loja
                    cursor.execute(f'SET search_path TO {schema_name}, public')
                    
                    # Verificar se as tabelas já existem
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = %s 
                        AND table_name LIKE 'cabeleireiro_%%'
                    """, [schema_name])
                    
                    existing_tables = [row[0] for row in cursor.fetchall()]
                    
                    if existing_tables:
                        self.stdout.write(f'  ✅ Tabelas já existem: {", ".join(existing_tables)}')
                    else:
                        self.stdout.write('  📦 Criando tabelas do cabeleireiro...')
                        
                        # Criar as tabelas manualmente
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS cabeleireiro_clientes (
                                id SERIAL PRIMARY KEY,
                                loja_id INTEGER NOT NULL,
                                nome VARCHAR(200) NOT NULL,
                                telefone VARCHAR(20) NOT NULL,
                                email VARCHAR(254),
                                cpf VARCHAR(14),
                                data_nascimento DATE,
                                observacoes TEXT,
                                is_active BOOLEAN DEFAULT TRUE,
                                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                            );
                            
                            CREATE TABLE IF NOT EXISTS cabeleireiro_profissionais (
                                id SERIAL PRIMARY KEY,
                                loja_id INTEGER NOT NULL,
                                nome VARCHAR(200) NOT NULL,
                                telefone VARCHAR(20) NOT NULL,
                                email VARCHAR(254),
                                especialidade VARCHAR(100),
                                comissao_percentual DECIMAL(5,2),
                                is_active BOOLEAN DEFAULT TRUE,
                                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                            );
                            
                            CREATE TABLE IF NOT EXISTS cabeleireiro_servicos (
                                id SERIAL PRIMARY KEY,
                                loja_id INTEGER NOT NULL,
                                nome VARCHAR(200) NOT NULL,
                                descricao TEXT,
                                duracao_minutos INTEGER NOT NULL,
                                preco DECIMAL(10,2) NOT NULL,
                                categoria VARCHAR(50),
                                is_active BOOLEAN DEFAULT TRUE,
                                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                            );
                            
                            CREATE TABLE IF NOT EXISTS cabeleireiro_agendamentos (
                                id SERIAL PRIMARY KEY,
                                loja_id INTEGER NOT NULL,
                                cliente_id INTEGER REFERENCES cabeleireiro_clientes(id) ON DELETE CASCADE,
                                profissional_id INTEGER REFERENCES cabeleireiro_profissionais(id) ON DELETE CASCADE,
                                servico_id INTEGER REFERENCES cabeleireiro_servicos(id) ON DELETE CASCADE,
                                data DATE NOT NULL,
                                horario TIME NOT NULL,
                                status VARCHAR(20) DEFAULT 'agendado',
                                observacoes TEXT,
                                valor_pago DECIMAL(10,2),
                                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                            );
                            
                            CREATE TABLE IF NOT EXISTS cabeleireiro_produtos (
                                id SERIAL PRIMARY KEY,
                                loja_id INTEGER NOT NULL,
                                nome VARCHAR(200) NOT NULL,
                                descricao TEXT,
                                categoria VARCHAR(50),
                                preco_custo DECIMAL(10,2),
                                preco_venda DECIMAL(10,2) NOT NULL,
                                estoque_atual INTEGER DEFAULT 0,
                                estoque_minimo INTEGER DEFAULT 0,
                                is_active BOOLEAN DEFAULT TRUE,
                                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                            );
                            
                            CREATE TABLE IF NOT EXISTS cabeleireiro_vendas (
                                id SERIAL PRIMARY KEY,
                                loja_id INTEGER NOT NULL,
                                cliente_id INTEGER REFERENCES cabeleireiro_clientes(id) ON DELETE SET NULL,
                                produto_id INTEGER REFERENCES cabeleireiro_produtos(id) ON DELETE CASCADE,
                                quantidade INTEGER NOT NULL,
                                valor_unitario DECIMAL(10,2) NOT NULL,
                                valor_total DECIMAL(10,2) NOT NULL,
                                forma_pagamento VARCHAR(20),
                                data_venda TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                            );
                            
                            CREATE TABLE IF NOT EXISTS cabeleireiro_funcionarios (
                                id SERIAL PRIMARY KEY,
                                loja_id INTEGER NOT NULL,
                                nome VARCHAR(200) NOT NULL,
                                email VARCHAR(254) NOT NULL,
                                telefone VARCHAR(20) NOT NULL,
                                cargo VARCHAR(100) NOT NULL,
                                data_admissao DATE DEFAULT CURRENT_DATE,
                                is_active BOOLEAN DEFAULT TRUE,
                                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                            );
                            
                            CREATE TABLE IF NOT EXISTS cabeleireiro_horariofuncionamento (
                                id SERIAL PRIMARY KEY,
                                loja_id INTEGER NOT NULL,
                                dia_semana INTEGER NOT NULL,
                                horario_abertura TIME NOT NULL,
                                horario_fechamento TIME NOT NULL,
                                is_active BOOLEAN DEFAULT TRUE
                            );
                            
                            CREATE TABLE IF NOT EXISTS cabeleireiro_bloqueioagenda (
                                id SERIAL PRIMARY KEY,
                                loja_id INTEGER NOT NULL,
                                profissional_id INTEGER REFERENCES cabeleireiro_profissionais(id) ON DELETE CASCADE,
                                data_inicio DATE NOT NULL,
                                data_fim DATE NOT NULL,
                                horario_inicio TIME,
                                horario_fim TIME,
                                motivo TEXT,
                                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                            );
                        """)
                        
                        self.stdout.write(self.style.SUCCESS('  ✅ Tabelas criadas com sucesso!'))
                    
                    # Resetar search_path
                    cursor.execute('SET search_path TO public')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Erro: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Processo concluído!'))
