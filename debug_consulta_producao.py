#!/usr/bin/env python3
"""
Script para debugar o problema de iniciar consulta em produção
"""

import subprocess
import json

def verificar_consulta(consulta_id):
    """Verifica o status de uma consulta específica"""
    print(f"🔍 Verificando Consulta ID {consulta_id}")
    print("=" * 35)
    
    try:
        result = subprocess.run([
            'curl', '-s', 
            f'https://lwksistemas-38ad47519238.herokuapp.com/api/clinica/consultas/{consulta_id}/'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                print(f"✅ Consulta encontrada:")
                print(f"   ID: {data['id']}")
                print(f"   Cliente: {data['cliente_nome']}")
                print(f"   Status: {data['status']}")
                print(f"   Data: {data['agendamento_data']} {data['agendamento_horario']}")
                return data
            except json.JSONDecodeError:
                print(f"❌ Resposta inválida: {result.stdout}")
                return None
        else:
            print(f"❌ Erro na requisição")
            return None
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

def tentar_iniciar_consulta(consulta_id):
    """Tenta iniciar uma consulta"""
    print(f"\n🚀 Tentando Iniciar Consulta ID {consulta_id}")
    print("=" * 40)
    
    try:
        result = subprocess.run([
            'curl', '-X', 'POST',
            f'https://lwksistemas-38ad47519238.herokuapp.com/api/clinica/consultas/{consulta_id}/iniciar_consulta/',
            '-H', 'Content-Type: application/json',
            '-s'
        ], capture_output=True, text=True)
        
        print(f"📊 Status Code: {result.returncode}")
        print(f"📄 Resposta: {result.stdout}")
        
        if result.stdout:
            try:
                data = json.loads(result.stdout)
                if 'error' in data:
                    print(f"❌ Erro: {data['error']}")
                else:
                    print(f"✅ Sucesso! Novo status: {data.get('status', 'N/A')}")
            except json.JSONDecodeError:
                print(f"📄 Resposta não-JSON: {result.stdout}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

def listar_todas_consultas():
    """Lista todas as consultas"""
    print("📋 Todas as Consultas")
    print("=" * 20)
    
    try:
        result = subprocess.run([
            'curl', '-s', 
            'https://lwksistemas-38ad47519238.herokuapp.com/api/clinica/consultas/'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            for consulta in data:
                print(f"   ID {consulta['id']}: {consulta['cliente_nome']} - {consulta['status']}")
            return data
        else:
            print("❌ Erro ao listar consultas")
            return []
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return []

def main():
    print("🏥 Debug - Sistema de Consultas em Produção")
    print("=" * 50)
    
    # Listar todas as consultas
    consultas = listar_todas_consultas()
    
    if consultas:
        # Pegar a primeira consulta agendada
        consulta_agendada = None
        for consulta in consultas:
            if consulta['status'] == 'agendada':
                consulta_agendada = consulta
                break
        
        if consulta_agendada:
            consulta_id = consulta_agendada['id']
            
            # Verificar detalhes da consulta
            verificar_consulta(consulta_id)
            
            # Tentar iniciar
            tentar_iniciar_consulta(consulta_id)
            
            # Verificar novamente após tentar iniciar
            print(f"\n🔄 Verificando Novamente Após Tentativa")
            verificar_consulta(consulta_id)
            
        else:
            print("❌ Nenhuma consulta agendada encontrada")
    
    print("\n🎯 Conclusão:")
    print("Se ainda há erro, pode ser:")
    print("1. Problema de sincronização no banco")
    print("2. Cache no Heroku")
    print("3. Problema na validação da view")

if __name__ == "__main__":
    main()