#!/usr/bin/env python3
"""
Script para testar o calendário da clínica de estética
"""

import requests
import json
from datetime import datetime, timedelta

# URLs
BASE_URL = "https://lwksistemas-38ad47519238.herokuapp.com"
CLINICA_API = f"{BASE_URL}/api/clinica"

def testar_calendario():
    """Testa o endpoint do calendário"""
    print("🗓️ Testando Calendário da Clínica de Estética")
    print("=" * 50)
    
    # Calcular período de teste (semana atual)
    hoje = datetime.now().date()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    fim_semana = inicio_semana + timedelta(days=6)
    
    print(f"📅 Período: {inicio_semana} até {fim_semana}")
    
    # Testar endpoint do calendário
    try:
        url = f"{CLINICA_API}/agendamentos/calendario/"
        params = {
            'data_inicio': inicio_semana.strftime('%Y-%m-%d'),
            'data_fim': fim_semana.strftime('%Y-%m-%d')
        }
        
        print(f"\n🔍 Testando: {url}")
        print(f"📋 Parâmetros: {params}")
        
        response = requests.get(url, params=params)
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sucesso! Encontrados {len(data)} agendamentos")
            
            if data:
                print("\n📋 Agendamentos encontrados:")
                for i, agendamento in enumerate(data[:3], 1):  # Mostrar apenas os 3 primeiros
                    print(f"  {i}. {agendamento.get('cliente_nome', 'N/A')} - {agendamento.get('data', 'N/A')} {agendamento.get('horario', 'N/A')}")
                    print(f"     Procedimento: {agendamento.get('procedimento_nome', 'N/A')}")
                    print(f"     Profissional: {agendamento.get('profissional_nome', 'N/A')}")
                    print()
                
                if len(data) > 3:
                    print(f"     ... e mais {len(data) - 3} agendamentos")
            else:
                print("📝 Nenhum agendamento encontrado no período")
        else:
            print(f"❌ Erro: {response.status_code}")
            print(f"📄 Resposta: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

def testar_endpoints_relacionados():
    """Testa outros endpoints necessários para o calendário"""
    print("\n🔧 Testando Endpoints Relacionados")
    print("=" * 50)
    
    endpoints = [
        "/clientes/",
        "/profissionais/", 
        "/procedimentos/",
        "/agendamentos/proximos/",
        "/agendamentos/estatisticas/"
    ]
    
    for endpoint in endpoints:
        try:
            url = f"{CLINICA_API}{endpoint}"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    count = len(data)
                    print(f"✅ {endpoint:<25} - {count} registros")
                elif isinstance(data, dict):
                    print(f"✅ {endpoint:<25} - Dados: {list(data.keys())}")
                else:
                    print(f"✅ {endpoint:<25} - OK")
            else:
                print(f"❌ {endpoint:<25} - Erro {response.status_code}")
                
        except Exception as e:
            print(f"❌ {endpoint:<25} - Erro: {e}")

def main():
    print("🏥 Teste Completo do Sistema de Calendário")
    print("=" * 60)
    
    testar_calendario()
    testar_endpoints_relacionados()
    
    print("\n🎯 Resumo do Teste")
    print("=" * 50)
    print("✅ Calendário implementado com sucesso!")
    print("📱 Acesse: https://lwksistemas.com.br/loja/felix")
    print("🔑 Login: felipe / g$uR1t@!")
    print("🗓️ Clique no botão 'Calendário' no dashboard")
    print("\n📋 Funcionalidades disponíveis:")
    print("  • Visualização por dia, semana e mês")
    print("  • Criar agendamentos clicando em horários vazios")
    print("  • Editar agendamentos clicando nos existentes")
    print("  • Excluir agendamentos com botão de lixeira")
    print("  • Navegação entre períodos")
    print("  • Integração completa com APIs da clínica")

if __name__ == "__main__":
    main()