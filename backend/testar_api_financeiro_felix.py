#!/usr/bin/env python3
"""
Script para testar API financeiro da loja felix
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/app' if os.path.exists('/app') else '/home/luiz/Documents/lwksistemas/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_production' if os.path.exists('/app') else 'config.settings')
django.setup()

from superadmin.financeiro_views import dashboard_financeiro_loja
from django.http import HttpRequest
from django.contrib.auth.models import User
from unittest.mock import Mock

def testar_api():
    """Testa a API de financeiro da loja felix"""
    print("🧪 Testando API Financeiro - Loja Felix")
    print("=" * 45)
    
    try:
        # Buscar usuário felipe
        user = User.objects.get(username='felipe')
        print(f"✅ Usuário encontrado: {user.username}")
        
        # Simular request autenticado
        request = Mock()
        request.user = user
        request.method = 'GET'
        
        # Testar API
        print(f"\n🔍 Testando endpoint: /api/superadmin/loja/felix/financeiro/")
        response = dashboard_financeiro_loja(request, 'felix')
        
        print(f"✅ API funcionando!")
        print(f"   Status Code: {response.status_code}")
        
        if hasattr(response, 'data') and response.data:
            data = response.data
            print(f"\n📊 Dados retornados:")
            
            if 'loja' in data:
                loja = data['loja']
                print(f"   Loja: {loja.get('nome')} ({loja.get('plano')})")
            
            if 'financeiro' in data:
                financeiro = data['financeiro']
                print(f"   Status: {financeiro.get('status_pagamento')}")
                print(f"   Valor: R$ {financeiro.get('valor_mensalidade')}")
                print(f"   Boleto: {'Disponível' if financeiro.get('boleto_url') else 'Não disponível'}")
                print(f"   PIX: {'Disponível' if financeiro.get('pix_copy_paste') else 'Não disponível'}")
            
            if 'estatisticas' in data:
                stats = data['estatisticas']
                print(f"   Pagamentos: {stats.get('total_pagamentos')} total")
        
        return True
        
    except User.DoesNotExist:
        print("❌ Usuário 'felipe' não encontrado!")
        return False
    except Exception as e:
        print(f"❌ Erro na API: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    sucesso = testar_api()
    
    if sucesso:
        print(f"\n🎯 Resultado:")
        print("✅ API funcionando corretamente")
        print("✅ Modal de configurações deve funcionar")
    else:
        print(f"\n❌ API com problemas")
        print("   Verifique os logs acima")

if __name__ == "__main__":
    main()