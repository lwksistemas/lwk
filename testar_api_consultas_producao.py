#!/usr/bin/env python3
"""
Script para testar a API de consultas em produção
"""

import requests
import json

def testar_api_consultas():
    """Testa a API de consultas em produção"""
    print("🏥 Testando API de Consultas em Produção")
    print("=" * 50)
    
    base_url = "https://lwksistemas-38ad47519238.herokuapp.com"
    
    # Testar endpoint de consultas
    try:
        print("📡 Testando GET /api/clinica/consultas/")
        response = requests.get(f"{base_url}/api/clinica/consultas/")
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sucesso! {len(data)} consultas encontradas")
            
            for consulta in data:
                print(f"   📋 ID: {consulta['id']} - {consulta['cliente_nome']} - Status: {consulta['status']}")
                print(f"      📅 {consulta['agendamento_data']} {consulta['agendamento_horario']}")
                print(f"      💆 {consulta['procedimento_nome']}")
                print(f"      👨‍⚕️ {consulta['profissional_nome']}")
                print(f"      📊 {consulta['total_evolucoes']} evolução(ões)")
                print()
        else:
            print(f"❌ Erro: {response.status_code}")
            print(f"📄 Resposta: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

def main():
    print("🌐 Teste da API de Consultas - Produção")
    print("=" * 45)
    
    testar_api_consultas()
    
    print("🎯 Teste concluído!")
    print("📱 Acesse: https://lwksistemas.com.br/loja/felix")
    print("🔑 Login: felipe / g$uR1t@!")

if __name__ == "__main__":
    main()