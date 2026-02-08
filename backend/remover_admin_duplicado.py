#!/usr/bin/env python
"""
Script para remover admin duplicado da Clínica Harmonis
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clinica_estetica.models import Funcionario

def remover_duplicados():
    """Remove funcionários duplicados, mantendo apenas um admin"""
    
    # Buscar loja Clínica Harmonis (ID 5898 do slug)
    from superadmin.models import Loja
    
    try:
        loja = Loja.objects.get(slug='clinica-harmonis-5898')
        print(f"✅ Loja encontrada: {loja.nome} (ID: {loja.id})")
    except Loja.DoesNotExist:
        print("❌ Loja não encontrada")
        return
    
    # Buscar funcionários admin duplicados
    admins = Funcionario.objects.filter(
        loja_id=loja.id,
        is_admin=True,
        email='pjluiz25@hotmail.com'
    ).order_by('id')
    
    print(f"\n📊 Total de admins encontrados: {admins.count()}")
    
    if admins.count() <= 1:
        print("✅ Não há duplicatas")
        return
    
    # Listar todos
    for admin in admins:
        print(f"\nID: {admin.id}")
        print(f"Nome: {admin.nome}")
        print(f"Email: {admin.email}")
        print(f"Cargo: {admin.cargo}")
        print(f"is_admin: {admin.is_admin}")
        print(f"is_active: {admin.is_active}")
    
    # Manter o primeiro (mais antigo), excluir os demais
    primeiro = admins.first()
    duplicados = admins.exclude(id=primeiro.id)
    
    print(f"\n🔧 Mantendo admin ID {primeiro.id}")
    print(f"🗑️ Removendo {duplicados.count()} duplicata(s)...")
    
    for dup in duplicados:
        print(f"   - Removendo ID {dup.id}")
        dup.delete()
    
    print("\n✅ Duplicatas removidas com sucesso!")
    
    # Verificar resultado final
    admins_final = Funcionario.objects.filter(
        loja_id=loja.id,
        is_admin=True
    )
    print(f"\n📊 Total de admins após limpeza: {admins_final.count()}")

if __name__ == '__main__':
    remover_duplicados()
