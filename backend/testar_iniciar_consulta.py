#!/usr/bin/env python3
"""
Script para testar a funcionalidade de iniciar consulta
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/home/luiz/Documents/lwksistemas/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clinica_estetica.models import Consulta
from clinica_estetica.views import ConsultaViewSet
from rest_framework.test import APIRequestFactory
from rest_framework.response import Response
from django.utils import timezone

def testar_iniciar_consulta():
    """Testa a funcionalidade de iniciar consulta"""
    print("🏥 Testando Iniciar Consulta")
    print("=" * 30)
    
    # Buscar uma consulta agendada
    consulta = Consulta.objects.filter(status='agendada').first()
    if not consulta:
        print("❌ Nenhuma consulta agendada encontrada")
        return
    
    print(f"📋 Consulta encontrada: {consulta.cliente.nome}")
    print(f"   ID: {consulta.id}")
    print(f"   Status atual: {consulta.status}")
    print(f"   Data: {consulta.agendamento.data} {consulta.agendamento.horario}")
    
    # Testar iniciar consulta
    factory = APIRequestFactory()
    request = factory.post(f'/clinica/consultas/{consulta.id}/iniciar_consulta/')
    
    viewset = ConsultaViewSet()
    viewset.request = request
    
    try:
        # Simular a ação de iniciar consulta
        if consulta.status != 'agendada':
            print("❌ Consulta deve estar agendada para ser iniciada")
            return
        
        consulta.status = 'em_andamento'
        consulta.data_inicio = timezone.now()
        consulta.save()
        
        print("✅ Consulta iniciada com sucesso!")
        print(f"   Novo status: {consulta.status}")
        print(f"   Data início: {consulta.data_inicio}")
        
        # Testar finalizar consulta
        print("\n🏁 Testando Finalizar Consulta")
        print("=" * 30)
        
        if consulta.status != 'em_andamento':
            print("❌ Consulta deve estar em andamento para ser finalizada")
            return
        
        consulta.status = 'concluida'
        consulta.data_fim = timezone.now()
        consulta.valor_pago = consulta.valor_consulta
        consulta.forma_pagamento = 'dinheiro'
        consulta.save()
        
        # Atualizar agendamento
        consulta.agendamento.status = 'concluido'
        consulta.agendamento.save()
        
        print("✅ Consulta finalizada com sucesso!")
        print(f"   Novo status: {consulta.status}")
        print(f"   Data fim: {consulta.data_fim}")
        print(f"   Valor pago: R$ {consulta.valor_pago}")
        
        # Resetar para teste
        consulta.status = 'agendada'
        consulta.data_inicio = None
        consulta.data_fim = None
        consulta.valor_pago = 0
        consulta.forma_pagamento = ''
        consulta.save()
        
        consulta.agendamento.status = 'agendado'
        consulta.agendamento.save()
        
        print("\n🔄 Consulta resetada para 'agendada' para novos testes")
        
    except Exception as e:
        print(f"❌ Erro ao testar consulta: {e}")
        import traceback
        traceback.print_exc()

def listar_consultas_por_status():
    """Lista consultas por status"""
    print("\n📊 Consultas por Status")
    print("=" * 25)
    
    for status_code, status_name in Consulta.STATUS_CHOICES:
        count = Consulta.objects.filter(status=status_code).count()
        print(f"   {status_name}: {count} consultas")

def main():
    print("🏥 Teste do Sistema de Consultas")
    print("=" * 35)
    
    listar_consultas_por_status()
    testar_iniciar_consulta()
    
    print("\n🎯 Conclusão:")
    print("Se os testes passaram, o problema pode estar:")
    print("1. Na API em produção (CORS, autenticação)")
    print("2. No frontend (JavaScript errors)")
    print("3. Na comunicação entre frontend e backend")

if __name__ == "__main__":
    main()