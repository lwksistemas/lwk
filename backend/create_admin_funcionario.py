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
    from django.db import connection
    
    # Usar query direta para evitar problemas com LojaIsolationManager
    # que depende do contexto da requisição (não disponível em scripts)
    with connection.cursor() as cursor:
        # Verificar se já existe (idempotência)
        cursor.execute("""
            SELECT id, nome FROM cabeleireiro_funcionarios 
            WHERE loja_id = %s AND email = %s
        """, [loja.id, loja.owner.email])
        
        funcionario_existente = cursor.fetchone()
        
        if funcionario_existente:
            return True, f"Administrador já cadastrado: {funcionario_existente[1]} (ID: {funcionario_existente[0]})"
        
        try:
            # Criar funcionário administrador usando query direta
            nome = loja.owner.get_full_name() or loja.owner.username
            data_admissao = loja.created_at.date() if hasattr(loja.created_at, 'date') else date.today()
            
            cursor.execute("""
                INSERT INTO cabeleireiro_funcionarios 
                (loja_id, nome, email, telefone, cargo, funcao, especialidade, comissao_percentual, data_admissao, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id, nome
            """, [
                loja.id,
                nome,
                loja.owner.email,
                '(00) 00000-0000',  # Telefone padrão
                'Proprietário',
                'administrador',
                '',  # especialidade vazia
                0.00,  # comissão 0
                data_admissao,
                True  # is_active
            ])
            
            resultado = cursor.fetchone()
            return True, f"Administrador criado: {resultado[1]} (ID: {resultado[0]})"
            
        except Exception as e:
            return False, f"Erro ao criar administrador: {e}"


def main():
    """Função principal do script"""
    print("=" * 70)
    print("🔧 Script ONE-TIME: Criar Administradores como Funcionários")
    print("=" * 70)
    print()
    
    # Buscar todas as lojas de cabeleireiro
    lojas_cabeleireiro = Loja.objects.filter(tipo_loja__nome='Cabeleireiro')
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

