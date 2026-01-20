#!/usr/bin/env python
"""
Script para limpar chamados de suporte de lojas que não existem mais
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_postgres')
django.setup()

from suporte.models import Chamado, RespostaChamado
from superadmin.models import Loja

print("=" * 60)
print("LIMPEZA: CHAMADOS ÓRFÃOS (LOJAS EXCLUÍDAS)")
print("=" * 60)

# 1. Buscar todos os chamados
print("\n1. Verificando chamados...")
todos_chamados = Chamado.objects.all()
print(f"   Total de chamados: {todos_chamados.count()}")

# 2. Buscar slugs de lojas ativas
print("\n2. Verificando lojas ativas...")
lojas_ativas = Loja.objects.values_list('slug', flat=True)
print(f"   Lojas ativas: {list(lojas_ativas)}")

# 3. Identificar chamados órfãos
print("\n3. Identificando chamados órfãos...")
chamados_orfaos = []
for chamado in todos_chamados:
    if chamado.loja_slug not in lojas_ativas:
        chamados_orfaos.append(chamado)
        print(f"   ⚠️  Chamado #{chamado.id}: {chamado.titulo} (Loja: {chamado.loja_nome} - {chamado.loja_slug})")

print(f"\n   Total de chamados órfãos: {len(chamados_orfaos)}")

# 4. Remover chamados órfãos
if chamados_orfaos:
    print("\n4. Removendo chamados órfãos...")
    confirmacao = input("   Deseja remover estes chamados? (s/n): ")
    
    if confirmacao.lower() == 's':
        total_respostas = 0
        for chamado in chamados_orfaos:
            respostas_count = chamado.respostas.count()
            total_respostas += respostas_count
            chamado.delete()
            print(f"   ✅ Chamado #{chamado.id} removido ({respostas_count} respostas)")
        
        print(f"\n   Total removido:")
        print(f"   - Chamados: {len(chamados_orfaos)}")
        print(f"   - Respostas: {total_respostas}")
    else:
        print("   ❌ Operação cancelada")
else:
    print("\n   ✅ Nenhum chamado órfão encontrado!")

# 5. Verificar resultado final
print("\n5. Verificando resultado...")
chamados_restantes = Chamado.objects.count()
print(f"   Chamados restantes: {chamados_restantes}")

print("\n" + "=" * 60)
print("✅ LIMPEZA CONCLUÍDA!")
print("=" * 60)
