#!/usr/bin/env python
"""
Script para testar o sistema de suporte
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from suporte.models import Chamado

print("=" * 60)
print("TESTE DO SISTEMA DE SUPORTE")
print("=" * 60)

try:
    # Tentar criar um chamado de teste
    print("\n1. Criando chamado de teste...")
    chamado = Chamado.objects.create(
        titulo="Teste de Sistema",
        descricao="Verificando se o sistema de suporte está funcionando",
        tipo="duvida",
        prioridade="baixa",
        loja_slug="sistema",
        loja_nome="Sistema",
        usuario_nome="Admin",
        usuario_email="admin@sistema.com"
    )
    print(f"✅ Chamado criado com sucesso! ID: {chamado.id}")
    
    # Listar chamados
    print("\n2. Listando chamados...")
    total = Chamado.objects.count()
    print(f"Total de chamados no banco: {total}")
    
    # Mostrar detalhes do chamado
    print(f"\nDetalhes do chamado:")
    print(f"  - ID: {chamado.id}")
    print(f"  - Título: {chamado.titulo}")
    print(f"  - Tipo: {chamado.get_tipo_display()}")
    print(f"  - Status: {chamado.get_status_display()}")
    print(f"  - Prioridade: {chamado.get_prioridade_display()}")
    print(f"  - Loja: {chamado.loja_nome}")
    print(f"  - Usuário: {chamado.usuario_nome}")
    
    # Deletar o teste
    print("\n3. Removendo chamado de teste...")
    chamado.delete()
    print("✅ Chamado de teste removido.")
    
    print("\n" + "=" * 60)
    print("✅ TESTE CONCLUÍDO COM SUCESSO!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ ERRO ao testar sistema: {e}")
    import traceback
    traceback.print_exc()
    print("\n" + "=" * 60)
    print("❌ TESTE FALHOU")
    print("=" * 60)
