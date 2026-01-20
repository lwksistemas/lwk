#!/usr/bin/env python3
"""
Script para testar diferentes formatos de cabeçalho de autenticação da API Asaas
"""

import requests
import json

# Chave de teste (sandbox)
API_KEY = '$aact_hmlg_000MzkwODA2MWY2OGM3MWRlMDU2NWM3MzJlNzZmNGZhZGY6OjY5ZjZhMmI3LTFmZWYtNDdkMC1iMmVkLTY4NWU0NzkxMmJlZDo6JGFhY2hfODYyMDJjYWYtZjY5Ny00OWM4LWI5NWItYmRmMjNjNDVkYmQ4'
BASE_URL = 'https://sandbox.asaas.com/api/v3'

def test_header_format(headers, format_name):
    """Testa um formato específico de cabeçalho"""
    print(f"\n🧪 Testando formato: {format_name}")
    print(f"   Headers: {headers}")
    
    try:
        response = requests.get(
            f"{BASE_URL}/customers?limit=1",
            headers=headers,
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ SUCESSO! Formato correto encontrado")
            data = response.json()
            print(f"   Resposta: {json.dumps(data, indent=2)[:200]}...")
            return True
        else:
            print(f"   ❌ Erro: {response.text[:100]}...")
            return False
            
    except Exception as e:
        print(f"   ❌ Exceção: {e}")
        return False

def main():
    print("🔍 Testando diferentes formatos de cabeçalho para API Asaas")
    print("=" * 60)
    
    # Formato 1: access_token (conforme documentação)
    headers1 = {
        'access_token': API_KEY,
        'Content-Type': 'application/json'
    }
    
    # Formato 2: Authorization Bearer
    headers2 = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Formato 3: Authorization com access_token
    headers3 = {
        'Authorization': f'access_token {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Formato 4: Authorization Basic
    headers4 = {
        'Authorization': f'Basic {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Formato 5: Apenas access_token sem Content-Type
    headers5 = {
        'access_token': API_KEY
    }
    
    # Formato 6: X-API-Key
    headers6 = {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
    }
    
    formats = [
        (headers1, "access_token header (documentação)"),
        (headers2, "Authorization: Bearer"),
        (headers3, "Authorization: access_token"),
        (headers4, "Authorization: Basic"),
        (headers5, "access_token sem Content-Type"),
        (headers6, "X-API-Key header")
    ]
    
    success_count = 0
    
    for headers, name in formats:
        if test_header_format(headers, name):
            success_count += 1
    
    print("\n" + "=" * 60)
    print(f"🎯 RESULTADO: {success_count} formato(s) funcionaram")
    
    if success_count == 0:
        print("❌ Nenhum formato funcionou. Possíveis problemas:")
        print("   - Chave API inválida ou expirada")
        print("   - Ambiente incorreto (sandbox vs produção)")
        print("   - Problema de conectividade")
        print("   - API do Asaas fora do ar")
    
    print("\n📋 Próximo passo:")
    print("   Usar o formato que funcionou no código Python")

if __name__ == "__main__":
    main()