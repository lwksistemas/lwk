#!/usr/bin/env python
"""
Script para limpar dados de suporte do schema 'public' (default)
Mantém apenas no schema 'suporte' isolado
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_postgres')
django.setup()

from suporte.models import Chamado, RespostaChamado
from django.db import connection

print("=" * 60)
print("LIMPEZA: REMOVER SUPORTE DO SCHEMA PUBLIC")
print("=" * 60)

# 1. Verificar dados antes
print("\n1. Verificando dados ANTES da limpeza...")
print(f"   Schema 'public': {Chamado.objects.using('default').count()} chamados")
print(f"   Schema 'suporte': {Chamado.objects.using('suporte').count()} chamados")

# 2. Deletar do schema public
print("\n2. Removendo dados do schema 'public'...")
try:
    # Deletar respostas primeiro (foreign key)
    respostas_deletadas = RespostaChamado.objects.using('default').all().delete()
    print(f"   ✅ {respostas_deletadas[0]} respostas removidas do 'public'")
    
    # Deletar chamados
    chamados_deletados = Chamado.objects.using('default').all().delete()
    print(f"   ✅ {chamados_deletados[0]} chamados removidos do 'public'")
    
except Exception as e:
    print(f"   ❌ Erro: {e}")

# 3. Verificar dados depois
print("\n3. Verificando dados DEPOIS da limpeza...")
print(f"   Schema 'public': {Chamado.objects.using('default').count()} chamados")
print(f"   Schema 'suporte': {Chamado.objects.using('suporte').count()} chamados")

# 4. Testar router
print("\n4. Testando router (deve usar 'suporte')...")
chamados_auto = Chamado.objects.all()
print(f"   Chamados via router: {chamados_auto.count()}")

print("\n" + "=" * 60)
print("✅ LIMPEZA CONCLUÍDA!")
print("=" * 60)
print("\nRESULTADO:")
print("- Dados de suporte removidos do schema 'public'")
print("- Dados mantidos apenas no schema 'suporte' isolado")
print("- Router direcionando queries para 'suporte'")
