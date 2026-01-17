#!/usr/bin/env python
"""
Script para criar tabelas de suporte no schema 'suporte' e migrar dados
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_postgres')
django.setup()

from django.db import connection
from django.core.management import call_command

print("=" * 60)
print("MIGRAÇÃO: CRIAR TABELAS NO SCHEMA SUPORTE")
print("=" * 60)

# 1. Criar tabelas no schema suporte
print("\n1. Criando tabelas no schema 'suporte'...")
with connection.cursor() as cursor:
    # Definir search_path para suporte
    cursor.execute("SET search_path TO suporte, public")
    
    # Criar tabela de chamados
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suporte_chamado (
            id SERIAL PRIMARY KEY,
            titulo VARCHAR(200) NOT NULL,
            descricao TEXT NOT NULL,
            tipo VARCHAR(20) NOT NULL DEFAULT 'duvida',
            status VARCHAR(20) NOT NULL DEFAULT 'aberto',
            prioridade VARCHAR(20) NOT NULL DEFAULT 'media',
            loja_slug VARCHAR(100) NOT NULL,
            loja_nome VARCHAR(200) NOT NULL,
            usuario_nome VARCHAR(200) NOT NULL,
            usuario_email VARCHAR(254) NOT NULL,
            atendente_id INTEGER,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            resolvido_em TIMESTAMP WITH TIME ZONE
        )
    """)
    print("   ✅ Tabela 'suporte_chamado' criada")
    
    # Criar tabela de respostas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suporte_respostachamado (
            id SERIAL PRIMARY KEY,
            chamado_id INTEGER NOT NULL REFERENCES suporte_chamado(id) ON DELETE CASCADE,
            usuario_nome VARCHAR(200) NOT NULL,
            mensagem TEXT NOT NULL,
            is_suporte BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)
    print("   ✅ Tabela 'suporte_respostachamado' criada")

# 2. Migrar dados do schema public para suporte
print("\n2. Migrando dados de 'public' para 'suporte'...")
with connection.cursor() as cursor:
    # Copiar chamados
    cursor.execute("""
        INSERT INTO suporte.suporte_chamado 
        SELECT * FROM public.suporte_chamado
        ON CONFLICT (id) DO NOTHING
    """)
    chamados_migrados = cursor.rowcount
    print(f"   ✅ {chamados_migrados} chamados migrados")
    
    # Copiar respostas
    cursor.execute("""
        INSERT INTO suporte.suporte_respostachamado 
        SELECT * FROM public.suporte_respostachamado
        ON CONFLICT (id) DO NOTHING
    """)
    respostas_migradas = cursor.rowcount
    print(f"   ✅ {respostas_migradas} respostas migradas")

# 3. Verificar resultado
print("\n3. Verificando resultado...")
with connection.cursor() as cursor:
    cursor.execute("SELECT COUNT(*) FROM suporte.suporte_chamado")
    total_chamados = cursor.fetchone()[0]
    print(f"   Chamados no schema 'suporte': {total_chamados}")
    
    cursor.execute("SELECT COUNT(*) FROM suporte.suporte_respostachamado")
    total_respostas = cursor.fetchone()[0]
    print(f"   Respostas no schema 'suporte': {total_respostas}")

print("\n" + "=" * 60)
print("✅ MIGRAÇÃO CONCLUÍDA!")
print("=" * 60)
print("\nPRÓXIMOS PASSOS:")
print("1. Testar sistema de suporte")
print("2. Se funcionar, remover tabelas do schema 'public'")
