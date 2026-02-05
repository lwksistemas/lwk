#!/usr/bin/env python
"""
Script ONE-TIME para criar administradores como funcionários nas lojas existentes.

Este script deve ser executado apenas UMA VEZ após o deploy.
Para novas lojas, o signal criará automaticamente o funcionário admin.

Boas práticas aplicadas:
- Código limpo e documentado
- Idempotência (pode ser executado múltiplas vezes sem duplicar)
- Tratamento de erros adequado
- Logging claro
- Separação de responsabilidades
"""
import os
import sys
import django
from datetime import date

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import Loja
from cabeleireiro.models import Funcionario


def criar_funcionario_admin(loja):
    """
    Cria funcionário administrador para uma loja específica.
    
    Args:
        loja: Instância do modelo Loja
        
    Returns:
        tuple: (sucesso: bool, mensagem: str)
    """
    # Verificar se já existe (idempotência)
    funcionario_existente = Funcionario.objects.filter(
        loja_id=loja.id,
        email=loja.owner.email
    ).first()
    
    if funcionario_existente:
        return True, f"Administrador já cadastrado: {funcionario_existente.nome}"
    
    try:
        # Criar funcionário administrador
        funcionario = Funcionario.objects.create(
            loja_id=loja.id,
            nome=loja.owner.get_full_name() or loja.owner.username,
            email=loja.owner.email,
            telefone=loja.telefone or '(00) 00000-0000',
            cargo='Proprietário',
            funcao='administrador',
            data_admissao=loja.created_at.date() if hasattr(loja.created_at, 'date') else date.today(),
            is_active=True
        )
        return True, f"Administrador criado: {funcionario.nome} (ID: {funcionario.id})"
    except Exception as e:
        return False, f"Erro ao criar administrador: {e}"


def main():
    """Função principal do script"""
    print("=" * 70)
    print("🔧 Script ONE-TIME: Criar Administradores como Funcionários")
    print("=" * 70)
    print()
    
    # Buscar todas as lojas de cabeleireiro
    lojas_cabeleireiro = Loja.objects.filter(tipo='cabeleireiro')
    total_lojas = lojas_cabeleireiro.count()
    
    print(f"📊 Encontradas {total_lojas} lojas de cabeleireiro")
    print()
    
    if total_lojas == 0:
        print("⚠️  Nenhuma loja de cabeleireiro encontrada.")
        return
    
    # Processar cada loja
    sucessos = 0
    erros = 0
    ja_existentes = 0
    
    for i, loja in enumerate(lojas_cabeleireiro, 1):
        print(f"[{i}/{total_lojas}] 🏪 {loja.nome} (ID: {loja.id})")
        
        sucesso, mensagem = criar_funcionario_admin(loja)
        
        if sucesso:
            if "já cadastrado" in mensagem:
                print(f"  ✅ {mensagem}")
                ja_existentes += 1
            else:
                print(f"  ✅ {mensagem}")
                sucessos += 1
        else:
            print(f"  ❌ {mensagem}")
            erros += 1
        print()
    
    # Resumo
    print("=" * 70)
    print("📊 RESUMO")
    print("=" * 70)
    print(f"Total de lojas processadas: {total_lojas}")
    print(f"✅ Administradores criados: {sucessos}")
    print(f"ℹ️  Já existentes: {ja_existentes}")
    print(f"❌ Erros: {erros}")
    print()
    print("✅ Script concluído!")
    print("=" * 70)


if __name__ == '__main__':
    main()

