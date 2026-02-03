"""
Comando para aplicar migrations no schema da loja 89 (cabeleireiro)
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Aplica migrations no schema da loja 89 (cabeleireiro)'

    def handle(self, *args, **options):
        schema_name = 'loja_89'
        
        self.stdout.write(f"Aplicando migrations no schema {schema_name}...")
        
        # Setar search_path para o schema da loja
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{schema_name}", public')
            
            # Aplicar migrations do app cabeleireiro
            self.stdout.write("Aplicando migrations do app cabeleireiro...")
            
            # SQL da migration 0001_initial.py
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS "cabeleireiro_clientes" (
                    "id" bigserial NOT NULL PRIMARY KEY,
                    "nome" varchar(200) NOT NULL,
                    "telefone" varchar(20) NOT NULL,
                    "email" varchar(254) NULL,
                    "cpf" varchar(14) NULL,
                    "data_nascimento" date NULL,
                    "endereco" text NULL,
                    "observacoes" text NULL,
                    "is_active" boolean NOT NULL,
                    "created_at" timestamp with time zone NOT NULL,
                    "updated_at" timestamp with time zone NOT NULL,
                    "loja_id" integer NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS "cabeleireiro_profissionais" (
                    "id" bigserial NOT NULL PRIMARY KEY,
                    "nome" varchar(200) NOT NULL,
                    "telefone" varchar(20) NOT NULL,
                    "email" varchar(254) NULL,
                    "especialidade" varchar(100) NULL,
                    "comissao_percentual" numeric(5, 2) NULL,
                    "is_active" boolean NOT NULL,
                    "created_at" timestamp with time zone NOT NULL,
                    "updated_at" timestamp with time zone NOT NULL,
                    "loja_id" integer NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS "cabeleireiro_servicos" (
                    "id" bigserial NOT NULL PRIMARY KEY,
                    "nome" varchar(200) NOT NULL,
                    "descricao" text NULL,
                    "preco" numeric(10, 2) NOT NULL,
                    "duracao_minutos" integer NOT NULL,
                    "categoria" varchar(50) NOT NULL,
                    "is_active" boolean NOT NULL,
                    "created_at" timestamp with time zone NOT NULL,
                    "updated_at" timestamp with time zone NOT NULL,
                    "loja_id" integer NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS "cabeleireiro_agendamentos" (
                    "id" bigserial NOT NULL PRIMARY KEY,
                    "data" date NOT NULL,
                    "horario" time NOT NULL,
                    "status" varchar(20) NOT NULL,
                    "observacoes" text NULL,
                    "valor" numeric(10, 2) NOT NULL,
                    "valor_pago" numeric(10, 2) NULL,
                    "forma_pagamento" varchar(20) NULL,
                    "created_at" timestamp with time zone NOT NULL,
                    "updated_at" timestamp with time zone NOT NULL,
                    "cliente_id" bigint NOT NULL REFERENCES "cabeleireiro_clientes" ("id"),
                    "profissional_id" bigint NOT NULL REFERENCES "cabeleireiro_profissionais" ("id"),
                    "servico_id" bigint NOT NULL REFERENCES "cabeleireiro_servicos" ("id"),
                    "loja_id" integer NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS "cabeleireiro_produtos" (
                    "id" bigserial NOT NULL PRIMARY KEY,
                    "nome" varchar(200) NOT NULL,
                    "descricao" text NULL,
                    "preco_custo" numeric(10, 2) NOT NULL,
                    "preco_venda" numeric(10, 2) NOT NULL,
                    "estoque_atual" integer NOT NULL,
                    "estoque_minimo" integer NOT NULL,
                    "categoria" varchar(50) NOT NULL,
                    "is_active" boolean NOT NULL,
                    "created_at" timestamp with time zone NOT NULL,
                    "updated_at" timestamp with time zone NOT NULL,
                    "loja_id" integer NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS "cabeleireiro_vendas" (
                    "id" bigserial NOT NULL PRIMARY KEY,
                    "data_venda" timestamp with time zone NOT NULL,
                    "quantidade" integer NOT NULL,
                    "valor_unitario" numeric(10, 2) NOT NULL,
                    "valor_total" numeric(10, 2) NOT NULL,
                    "forma_pagamento" varchar(20) NOT NULL,
                    "created_at" timestamp with time zone NOT NULL,
                    "updated_at" timestamp with time zone NOT NULL,
                    "cliente_id" bigint NULL REFERENCES "cabeleireiro_clientes" ("id"),
                    "produto_id" bigint NOT NULL REFERENCES "cabeleireiro_produtos" ("id"),
                    "loja_id" integer NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS "cabeleireiro_funcionarios" (
                    "id" bigserial NOT NULL PRIMARY KEY,
                    "nome" varchar(200) NOT NULL,
                    "email" varchar(254) NOT NULL UNIQUE,
                    "telefone" varchar(20) NOT NULL,
                    "cargo" varchar(100) NOT NULL,
                    "salario" numeric(10, 2) NULL,
                    "data_admissao" date NOT NULL,
                    "is_active" boolean NOT NULL,
                    "created_at" timestamp with time zone NOT NULL,
                    "updated_at" timestamp with time zone NOT NULL,
                    "loja_id" integer NOT NULL,
                    "user_id" integer NULL
                );
                
                CREATE TABLE IF NOT EXISTS "cabeleireiro_horariofuncionamento" (
                    "id" bigserial NOT NULL PRIMARY KEY,
                    "dia_semana" integer NOT NULL,
                    "horario_abertura" time NOT NULL,
                    "horario_fechamento" time NOT NULL,
                    "is_active" boolean NOT NULL,
                    "created_at" timestamp with time zone NOT NULL,
                    "updated_at" timestamp with time zone NOT NULL,
                    "loja_id" integer NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS "cabeleireiro_bloqueioagenda" (
                    "id" bigserial NOT NULL PRIMARY KEY,
                    "data_inicio" date NOT NULL,
                    "data_fim" date NOT NULL,
                    "horario_inicio" time NULL,
                    "horario_fim" time NULL,
                    "motivo" varchar(200) NOT NULL,
                    "is_active" boolean NOT NULL,
                    "created_at" timestamp with time zone NOT NULL,
                    "updated_at" timestamp with time zone NOT NULL,
                    "profissional_id" bigint NULL REFERENCES "cabeleireiro_profissionais" ("id"),
                    "loja_id" integer NOT NULL
                );
            """)
            
            self.stdout.write(self.style.SUCCESS(f'✅ Migrations aplicadas no schema {schema_name}'))
