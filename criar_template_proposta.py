#!/usr/bin/env python3
"""
Script para criar templates de propostas via API
Uso: python criar_template_proposta.py
"""

import requests
import json

# Configurações
API_URL = "https://lwksistemas.com.br/api/crm-vendas/proposta-templates/"
TOKEN = input("Cole seu token de autenticação: ").strip()

# Headers
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("\n=== Criar Template de Proposta ===\n")

# Dados do template
nome = input("Nome do template (ex: Proposta Padrão): ").strip()
print("\nConteúdo do template (pressione Ctrl+D quando terminar):")
print("(Cole o texto da proposta abaixo)")
conteudo_lines = []
try:
    while True:
        line = input()
        conteudo_lines.append(line)
except EOFError:
    pass

conteudo = "\n".join(conteudo_lines)

is_padrao = input("\nMarcar como padrão? (s/n): ").strip().lower() == 's'

# Payload
payload = {
    "nome": nome,
    "conteudo": conteudo,
    "is_padrao": is_padrao,
    "ativo": True
}

# Fazer requisição
print("\nCriando template...")
try:
    response = requests.post(API_URL, headers=headers, json=payload)
    response.raise_for_status()
    
    template = response.json()
    print("\n✅ Template criado com sucesso!")
    print(f"ID: {template['id']}")
    print(f"Nome: {template['nome']}")
    print(f"Padrão: {'Sim' if template['is_padrao'] else 'Não'}")
    
except requests.exceptions.HTTPError as e:
    print(f"\n❌ Erro ao criar template: {e}")
    print(f"Resposta: {e.response.text}")
except Exception as e:
    print(f"\n❌ Erro: {e}")
