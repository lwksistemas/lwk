#!/usr/bin/env python3
import requests
import json

# Fazer login
login_data = {
    "username": "felipe",
    "password": "147Luiz@"
}

response = requests.post("https://lwksistemas-38ad47519238.herokuapp.com/api/auth/token/", 
                        json=login_data)

if response.status_code == 200:
    token_data = response.json()
    access_token = token_data['access']
    print(f"✅ Login realizado com sucesso")
    print(f"Token: {access_token[:50]}...")
    
    # Verificar informações da loja felix
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Tentar acessar dados da loja felix
    loja_response = requests.get("https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/loja/felix/financeiro/", 
                                headers=headers)
    
    print(f"\n📊 Tentativa de acesso aos dados financeiros:")
    print(f"Status: {loja_response.status_code}")
    print(f"Response: {loja_response.text}")
    
    # Verificar informações públicas da loja
    public_response = requests.get("https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/lojas/info_publica/?slug=felix")
    print(f"\n🔍 Informações públicas da loja felix:")
    print(f"Status: {public_response.status_code}")
    print(f"Response: {public_response.text}")
    
else:
    print(f"❌ Erro no login: {response.status_code}")
    print(f"Response: {response.text}")