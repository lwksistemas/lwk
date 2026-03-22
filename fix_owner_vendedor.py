#!/usr/bin/env python
"""
Script para remover VendedorUsuario do owner da loja.
Isso corrige o problema de perfil intermitente (Admin → Vendedor).
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
django.setup()

from superadmin.models import Loja, VendedorUsuario

def fix_owner_vendedor(cpf_cnpj):
    """Remove VendedorUsuario do owner da loja."""
    print(f"\n{'='*60}")
    print(f"🔧 CORRIGINDO PROBLEMA: {cpf_cnpj}")
    print(f"{'='*60}\n")
    
    # Buscar loja
    try:
        loja = Loja.objects.using('default').select_related('owner').get(cpf_cnpj=cpf_cnpj)
    except Loja.DoesNotExist:
        print(f"❌ ERRO: Loja com CPF/CNPJ {cpf_cnpj} não encontrada")
        return
    
    owner = loja.owner
    
    print(f"✅ Loja: {loja.nome} (ID: {loja.id})")
    print(f"✅ Owner: {owner.username} (ID: {owner.id})")
    
    # Verificar se owner tem VendedorUsuario
    vu_list = VendedorUsuario.objects.using('default').filter(
        user=owner,
        loja=loja
    )
    
    count = vu_list.count()
    
    if count == 0:
        print(f"\n✅ OK: Owner NÃO tem VendedorUsuario vinculado")
        print(f"   Nenhuma ação necessária.")
        return
    
    print(f"\n⚠️ ATENÇÃO: Encontrados {count} VendedorUsuario(s) vinculado(s) ao owner")
    print(f"\n🗑️ Removendo VendedorUsuario do owner...")
    
    # Remover VendedorUsuario
    deleted_count, _ = vu_list.delete()
    
    print(f"\n✅ SUCESSO: {deleted_count} VendedorUsuario(s) removido(s)")
    print(f"\n{'='*60}")
    print(f"✅ CORREÇÃO CONCLUÍDA")
    print(f"{'='*60}\n")
    print(f"Próximos passos:")
    print(f"1. Pedir ao usuário para limpar sessionStorage:")
    print(f"   - Abrir DevTools → Application → Session Storage")
    print(f"   - Remover: is_vendedor, current_vendedor_id, user_role")
    print(f"2. Fazer logout e login novamente")
    print(f"3. Verificar se tem acesso a configurações e relatórios")
    print(f"4. Monitorar por 24h para confirmar que problema foi resolvido")
    print(f"\n{'='*60}\n")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python fix_owner_vendedor.py <CPF_CNPJ>")
        print("Exemplo: python fix_owner_vendedor.py 41449198000172")
        sys.exit(1)
    
    cpf_cnpj = sys.argv[1]
    fix_owner_vendedor(cpf_cnpj)
