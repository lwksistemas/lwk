#!/usr/bin/env python
"""
Script para sincronizar pagamento da Clinica Felipe (1845) com Mercado Pago
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from superadmin.models import Loja
from superadmin.sync_service import sync_mercadopago_payments

def main():
    print("=" * 80)
    print("SINCRONIZAÇÃO: Clinica Felipe (1845) - Mercado Pago")
    print("=" * 80)
    
    try:
        loja = Loja.objects.get(slug='clinica-felipe-1845')
        print(f"\n✅ Loja encontrada: {loja.nome}")
        print(f"   Email: {loja.owner.email}")
        print(f"   Status financeiro: {loja.financeiro.status_pagamento}")
        print(f"   Senha enviada: {loja.financeiro.senha_enviada}")
        
        # IDs dos pagamentos
        pix_id = "147748353282"
        boleto_id = "147748631038"
        
        print(f"\n📋 IDs dos Pagamentos:")
        print(f"   PIX: {pix_id}")
        print(f"   Boleto: {boleto_id}")
        
        # Sincronizar pagamentos
        print(f"\n🔄 Sincronizando pagamentos com Mercado Pago...")
        result = sync_mercadopago_payments(loja.slug)
        
        print(f"\n✅ Sincronização concluída!")
        print(f"   Pagamentos processados: {result.get('processed', 0)}")
        print(f"   Mensagem: {result.get('message', 'N/A')}")
        
        # Verificar status após sincronização
        loja.refresh_from_db()
        print(f"\n📊 Status após sincronização:")
        print(f"   Status financeiro: {loja.financeiro.status_pagamento}")
        print(f"   Senha enviada: {loja.financeiro.senha_enviada}")
        print(f"   Último pagamento: {loja.financeiro.ultimo_pagamento}")
        
        if loja.financeiro.status_pagamento == 'ativo':
            print(f"\n✅ SUCESSO! Loja ativada.")
        else:
            print(f"\n⚠️ ATENÇÃO: Loja ainda não está ativa.")
            print(f"   Verifique se o pagamento foi aprovado no Mercado Pago.")
        
    except Loja.DoesNotExist:
        print("\n❌ ERRO: Loja 'clinica-felipe-1845' não encontrada!")
        return
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
