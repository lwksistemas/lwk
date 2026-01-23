"""
Script para popular loja_id ANTES de criar as migrations

IMPORTANTE: Executar ANTES de makemigrations
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import Loja

def main():
    print("=" * 80)
    print("🔧 PREPARAÇÃO PARA MIGRATION - Popular loja_id")
    print("=" * 80)
    
    # Listar lojas disponíveis
    lojas = Loja.objects.filter(is_active=True)
    
    if not lojas.exists():
        print("\n❌ ERRO: Nenhuma loja ativa encontrada!")
        print("   Crie pelo menos uma loja antes de continuar.")
        return
    
    print(f"\n📋 Lojas disponíveis:")
    for loja in lojas:
        print(f"   {loja.id}. {loja.nome} ({loja.slug}) - {loja.tipo_loja.nome if loja.tipo_loja else 'Sem tipo'}")
    
    print("\n" + "=" * 80)
    print("✅ PREPARAÇÃO CONCLUÍDA")
    print("=" * 80)
    print("\n📝 PRÓXIMOS PASSOS:")
    print("   1. Execute: python manage.py makemigrations")
    print("   2. Quando pedir default, digite: 1")
    print("   3. Digite: 1 (para usar loja_id=1 como padrão)")
    print("   4. Execute: python manage.py migrate")
    print("   5. Execute: python popular_loja_id_corrigir.py (para corrigir os dados)")
    print("\n")

if __name__ == '__main__':
    main()
