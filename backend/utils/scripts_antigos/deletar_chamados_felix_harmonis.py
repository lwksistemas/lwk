#!/usr/bin/env python
"""
Script para deletar chamados das lojas Felix e Harmonis
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_postgres')
django.setup()

from suporte.models import Chamado

print("=" * 60)
print("DELETAR CHAMADOS: FELIX E HARMONIS")
print("=" * 60)

# Buscar chamados das lojas Felix e Harmonis
chamados_felix = Chamado.objects.filter(loja_slug='felix')
chamados_harmonis = Chamado.objects.filter(loja_slug='harmonis')

print(f"\nChamados encontrados:")
print(f"  Felix: {chamados_felix.count()}")
print(f"  Harmonis: {chamados_harmonis.count()}")

# Deletar
total_deletado = 0
respostas_deletadas = 0

for chamado in chamados_felix:
    respostas_deletadas += chamado.respostas.count()
    chamado.delete()
    total_deletado += 1
    print(f"  ✅ Deletado: #{chamado.id} - {chamado.titulo}")

for chamado in chamados_harmonis:
    respostas_deletadas += chamado.respostas.count()
    chamado.delete()
    total_deletado += 1
    print(f"  ✅ Deletado: #{chamado.id} - {chamado.titulo}")

print(f"\n✅ Total deletado:")
print(f"  Chamados: {total_deletado}")
print(f"  Respostas: {respostas_deletadas}")

# Verificar restantes
restantes = Chamado.objects.count()
print(f"\nChamados restantes no sistema: {restantes}")

print("\n" + "=" * 60)
print("✅ CONCLUÍDO!")
print("=" * 60)
