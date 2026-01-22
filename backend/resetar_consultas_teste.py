#!/usr/bin/env python3
"""
Script para resetar consultas para status agendada para testes
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/home/luiz/Documents/lwksistemas/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clinica_estetica.models import Consulta

def resetar_consultas():
    """Reseta consultas para status agendada"""
    print("🔄 Resetando Consultas para Teste")
    print("=" * 35)
    
    consultas = Consulta.objects.all()
    
    for consulta in consultas:
        print(f"📋 Consulta ID {consulta.id}: {consulta.cliente.nome}")
        print(f"   Status atual: {consulta.status}")
        
        # Resetar para agendada
        consulta.status = 'agendada'
        consulta.data_inicio = None
        consulta.data_fim = None
        consulta.valor_pago = 0
        consulta.forma_pagamento = ''
        consulta.observacoes_gerais = ''
        consulta.save()
        
        # Resetar agendamento também
        consulta.agendamento.status = 'agendado'
        consulta.agendamento.save()
        
        print(f"   ✅ Resetada para: agendada")
        print()

def main():
    print("🏥 Reset de Consultas para Teste")
    print("=" * 35)
    
    resetar_consultas()
    
    print("🎯 Todas as consultas foram resetadas para 'agendada'")
    print("📱 Agora você pode testar:")
    print("1. Iniciar consulta")
    print("2. Finalizar consulta")
    print("3. Registrar evolução")

if __name__ == "__main__":
    main()