#!/usr/bin/env python
"""
Script para criar chamados de teste no schema 'suporte'
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_postgres')
django.setup()

from suporte.models import Chamado, RespostaChamado

print("=" * 60)
print("CRIAR CHAMADOS DE TESTE NO SCHEMA SUPORTE")
print("=" * 60)

# 1. Criar chamados de teste
print("\n1. Criando chamados de teste...")
chamados_teste = [
    {
        'titulo': 'Dúvida sobre sistema',
        'descricao': 'Como faço para adicionar um novo produto?',
        'tipo': 'duvida',
        'prioridade': 'baixa',
        'loja_slug': 'harmonis',
        'loja_nome': 'Harmonis',
        'usuario_nome': 'Daniel Souza Felix',
        'usuario_email': 'pjluiz25@hotmail.com'
    },
    {
        'titulo': 'Problema no login',
        'descricao': 'Não consigo fazer login no sistema',
        'tipo': 'problema',
        'prioridade': 'alta',
        'loja_slug': 'felix',
        'loja_nome': 'Felix',
        'usuario_nome': 'João Silva',
        'usuario_email': 'joao@felix.com'
    },
    {
        'titulo': 'Solicitação de treinamento',
        'descricao': 'Gostaria de um treinamento sobre relatórios',
        'tipo': 'treinamento',
        'prioridade': 'media',
        'loja_slug': 'harmonis',
        'loja_nome': 'Harmonis',
        'usuario_nome': 'Maria Santos',
        'usuario_email': 'maria@harmonis.com'
    }
]

for dados in chamados_teste:
    chamado = Chamado.objects.create(**dados)
    print(f"   ✅ Chamado #{chamado.id} criado: {chamado.titulo}")

# 2. Verificar chamados criados
print("\n2. Verificando chamados no schema 'suporte'...")
total = Chamado.objects.count()
print(f"   Total de chamados: {total}")

# 3. Listar chamados
print("\n3. Listando chamados:")
for chamado in Chamado.objects.all():
    print(f"   - #{chamado.id}: {chamado.titulo}")
    print(f"     Loja: {chamado.loja_nome} | Status: {chamado.status}")
    print(f"     Tipo: {chamado.tipo} | Prioridade: {chamado.prioridade}")

print("\n" + "=" * 60)
print("✅ CHAMADOS DE TESTE CRIADOS!")
print("=" * 60)
print("\nPRÓXIMOS PASSOS:")
print("1. Testar sistema de suporte no frontend")
print("2. Verificar se chamados aparecem nos dashboards")
