#!/usr/bin/env python3
"""
Script para testar a funcionalidade de agenda por profissional
"""

import requests
import json
from datetime import datetime, timedelta

# Configurações
BASE_URL = "https://lwksistemas-38ad47519238.herokuapp.com"
USERNAME = "felipe"
PASSWORD = "147Luiz@"

def fazer_login():
    """Faz login e retorna o token de acesso"""
    url = f"{BASE_URL}/api/auth/token/"
    data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json()['access']
    else:
        print(f"Erro no login: {response.status_code}")
        print(response.text)
        return None

def criar_agendamentos_teste(token):
    """Cria agendamentos de teste para diferentes profissionais"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Agendamentos para hoje e próximos dias
    hoje = datetime.now().date()
    
    agendamentos = [
        {
            "cliente": 9,  # Luiz Felix
            "profissional": 4,  # Dra. Maria Santos
            "procedimento": 5,  # Limpeza de Pele
            "data": str(hoje),
            "horario": "09:00:00",
            "status": "agendado",
            "valor": "100.00",
            "observacoes": "Agendamento teste - agenda profissional"
        },
        {
            "cliente": 6,  # Teste Debug
            "profissional": 4,  # Dra. Maria Santos
            "procedimento": 8,  # Hidratação Facial
            "data": str(hoje),
            "horario": "10:00:00",
            "status": "agendado",
            "valor": "90.00",
            "observacoes": "Agendamento teste - agenda profissional"
        },
        {
            "cliente": 7,  # Cliente Novo
            "profissional": 5,  # Nayara Souza
            "procedimento": 7,  # Massagem Relaxante
            "data": str(hoje),
            "horario": "14:00:00",
            "status": "agendado",
            "valor": "120.00",
            "observacoes": "Agendamento teste - agenda profissional"
        },
        {
            "cliente": 9,  # Luiz Felix
            "profissional": 5,  # Nayara Souza
            "procedimento": 5,  # Limpeza de Pele
            "data": str(hoje + timedelta(days=1)),
            "horario": "11:00:00",
            "status": "agendado",
            "valor": "100.00",
            "observacoes": "Agendamento teste - agenda profissional"
        }
    ]
    
    print("🔄 Criando agendamentos de teste...")
    for agendamento in agendamentos:
        url = f"{BASE_URL}/api/clinica/agendamentos/"
        response = requests.post(url, json=agendamento, headers=headers)
        
        if response.status_code == 201:
            print(f"✅ Agendamento criado: {agendamento['data']} {agendamento['horario']} - Prof. {agendamento['profissional']}")
        else:
            print(f"❌ Erro ao criar agendamento: {response.status_code}")
            print(response.text)

def criar_bloqueio_teste(token):
    """Cria um bloqueio de teste"""
    headers = {"Authorization": f"Bearer {token}"}
    
    hoje = datetime.now().date()
    amanha = hoje + timedelta(days=1)
    
    bloqueio = {
        "profissional": 4,  # Dra. Maria Santos
        "data_inicio": str(hoje),
        "data_fim": str(hoje),
        "horario_inicio": "12:00:00",
        "horario_fim": "13:00:00",
        "motivo": "Almoço - Bloqueio de teste",
        "tipo": "bloqueio"
    }
    
    print("🔄 Criando bloqueio de teste...")
    url = f"{BASE_URL}/api/clinica/bloqueios/"
    response = requests.post(url, json=bloqueio, headers=headers)
    
    if response.status_code == 201:
        print(f"✅ Bloqueio criado: {bloqueio['data_inicio']} {bloqueio['horario_inicio']}-{bloqueio['horario_fim']}")
    else:
        print(f"❌ Erro ao criar bloqueio: {response.status_code}")
        print(response.text)

def testar_filtros(token):
    """Testa os filtros da agenda"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n🔍 Testando filtros da agenda...")
    
    # Testar filtro por profissional
    print("\n📋 Agendamentos da Dra. Maria Santos (ID: 4):")
    url = f"{BASE_URL}/api/clinica/agendamentos/?profissional_id=4"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        agendamentos = response.json()
        for ag in agendamentos[:3]:  # Mostrar apenas os 3 primeiros
            print(f"  - {ag['data']} {ag['horario']} - {ag['cliente_nome']} - {ag['procedimento_nome']}")
    
    print("\n📋 Agendamentos da Nayara Souza (ID: 5):")
    url = f"{BASE_URL}/api/clinica/agendamentos/?profissional_id=5"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        agendamentos = response.json()
        for ag in agendamentos[:3]:  # Mostrar apenas os 3 primeiros
            print(f"  - {ag['data']} {ag['horario']} - {ag['cliente_nome']} - {ag['procedimento_nome']}")
    
    # Testar bloqueios
    print("\n🚫 Bloqueios cadastrados:")
    url = f"{BASE_URL}/api/clinica/bloqueios/"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        bloqueios = response.json()
        if bloqueios:
            for bloqueio in bloqueios:
                print(f"  - {bloqueio['data_inicio']} - {bloqueio['motivo']}")
        else:
            print("  Nenhum bloqueio encontrado")

def main():
    print("🧪 TESTE DA AGENDA POR PROFISSIONAL")
    print("=" * 50)
    
    # Fazer login
    token = fazer_login()
    if not token:
        print("❌ Falha no login")
        return
    
    print("✅ Login realizado com sucesso")
    
    # Criar dados de teste
    criar_agendamentos_teste(token)
    criar_bloqueio_teste(token)
    
    # Testar filtros
    testar_filtros(token)
    
    print("\n" + "=" * 50)
    print("✅ TESTE CONCLUÍDO!")
    print("\n📱 Acesse: https://lwksistemas.com.br/loja/felix/dashboard")
    print("🔑 Login: felipe / 147Luiz@")
    print("📅 Clique em 'Sistema de Consultas' > 'Agenda por Profissional'")

if __name__ == "__main__":
    main()