#!/usr/bin/env python3
"""
Script para vincular administradores de lojas existentes como funcionários
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import Loja
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)

def vincular_admins_como_funcionarios():
    """Vincula administradores de lojas existentes como funcionários"""
    print("🔄 Vinculando administradores como funcionários...")
    print("=" * 60)
    
    lojas = Loja.objects.select_related('tipo_loja', 'owner').all()
    
    total_lojas = lojas.count()
    funcionarios_criados = 0
    funcionarios_existentes = 0
    erros = 0
    
    for loja in lojas:
        try:
            tipo_loja_nome = loja.tipo_loja.nome
            owner = loja.owner
            
            print(f"\n📋 Loja: {loja.nome}")
            print(f"   Tipo: {tipo_loja_nome}")
            print(f"   Admin: {owner.username}")
            
            # Dados básicos do funcionário
            funcionario_data = {
                'user': owner,
                'nome': owner.get_full_name() or owner.username,
                'email': owner.email,
                'telefone': '',
                'cargo': 'Administrador'
            }
            
            funcionario_criado = False
            
            # Criar funcionário baseado no tipo de loja
            if tipo_loja_nome == 'Clínica de Estética':
                from clinica_estetica.models import Funcionario
                
                if Funcionario.objects.filter(user=owner).exists():
                    print(f"   ℹ️  Funcionário já existe")
                    funcionarios_existentes += 1
                else:
                    Funcionario.objects.create(**funcionario_data)
                    print(f"   ✅ Funcionário criado")
                    funcionarios_criados += 1
                    funcionario_criado = True
                    
            elif tipo_loja_nome == 'Serviços':
                from servicos.models import Funcionario
                
                if Funcionario.objects.filter(user=owner).exists():
                    print(f"   ℹ️  Funcionário já existe")
                    funcionarios_existentes += 1
                else:
                    Funcionario.objects.create(**funcionario_data)
                    print(f"   ✅ Funcionário criado")
                    funcionarios_criados += 1
                    funcionario_criado = True
                    
            elif tipo_loja_nome == 'Restaurante':
                from restaurante.models import Funcionario
                
                if Funcionario.objects.filter(user=owner).exists():
                    print(f"   ℹ️  Funcionário já existe")
                    funcionarios_existentes += 1
                else:
                    funcionario_data['cargo'] = 'Gerente'
                    Funcionario.objects.create(**funcionario_data)
                    print(f"   ✅ Funcionário criado (Gerente)")
                    funcionarios_criados += 1
                    funcionario_criado = True
                    
            elif tipo_loja_nome == 'CRM Vendas':
                from crm_vendas.models import Vendedor
                
                if Vendedor.objects.filter(user=owner).exists():
                    print(f"   ℹ️  Vendedor já existe")
                    funcionarios_existentes += 1
                else:
                    funcionario_data['cargo'] = 'Gerente de Vendas'
                    funcionario_data['meta_mensal'] = 10000.00
                    Vendedor.objects.create(**funcionario_data)
                    print(f"   ✅ Vendedor criado")
                    funcionarios_criados += 1
                    funcionario_criado = True
                    
            elif tipo_loja_nome == 'E-commerce':
                print(f"   ℹ️  E-commerce não possui modelo de funcionário")
                
            else:
                print(f"   ⚠️  Tipo de loja não reconhecido: {tipo_loja_nome}")
                
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            erros += 1
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("📊 RESUMO")
    print("=" * 60)
    print(f"Total de lojas processadas: {total_lojas}")
    print(f"✅ Funcionários criados: {funcionarios_criados}")
    print(f"ℹ️  Funcionários já existentes: {funcionarios_existentes}")
    print(f"❌ Erros: {erros}")
    print("=" * 60)
    
    if funcionarios_criados > 0:
        print("\n✅ Administradores vinculados como funcionários com sucesso!")
    else:
        print("\nℹ️  Nenhum funcionário novo foi criado (todos já existiam)")

if __name__ == "__main__":
    vincular_admins_como_funcionarios()