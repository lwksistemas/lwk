#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import Loja
from clinica_estetica.models import Funcionario

def criar_admin_clinica():
    """Cria admin para a Clínica Harmonis"""
    
    try:
        # Buscar a loja
        loja = Loja.objects.get(slug='clinica-harmonis-5898')
        print(f"✅ Loja encontrada: {loja.nome}")
        print(f"   Owner: {loja.owner.username} ({loja.owner.email})")
        
        # Verificar funcionários existentes
        funcionarios = Funcionario.objects.filter(loja_id=loja.id)
        print(f"\n📋 Funcionários existentes: {funcionarios.count()}")
        for f in funcionarios:
            print(f"   - {f.nome} ({f.cargo}) - is_admin: {f.is_admin}")
        
        # Verificar se já existe admin
        admin_existente = funcionarios.filter(is_admin=True).first()
        if admin_existente:
            print(f"\n✅ Admin já existe: {admin_existente.nome}")
            return
        
        # Criar admin
        admin = Funcionario.objects.create(
            nome=loja.owner.get_full_name() or loja.owner.username,
            email=loja.owner.email,
            telefone='',
            cargo='Administrador',
            is_admin=True,
            is_active=True,
            loja_id=loja.id
        )
        
        print(f"\n✅ Admin criado com sucesso!")
        print(f"   Nome: {admin.nome}")
        print(f"   Email: {admin.email}")
        print(f"   Cargo: {admin.cargo}")
        print(f"   is_admin: {admin.is_admin}")
        
    except Loja.DoesNotExist:
        print("❌ Loja não encontrada!")
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    criar_admin_clinica()
