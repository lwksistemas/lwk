#!/usr/bin/env python3
"""
Script para preparar consultas em diferentes status para teste
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/home/luiz/Documents/lwksistemas/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clinica_estetica.models import Consulta
from django.utils import timezone

def preparar_consultas_teste():
    """Prepara consultas em diferentes status para teste completo"""
    print("🏥 Preparando Consultas para Teste")
    print("=" * 35)
    
    consultas = Consulta.objects.all().order_by('id')
    
    if len(consultas) < 3:
        print("❌ Precisa de pelo menos 3 consultas para teste")
        return
    
    # Consulta 1: Agendada (para testar iniciar)
    consulta1 = consultas[0]
    consulta1.status = 'agendada'
    consulta1.data_inicio = None
    consulta1.data_fim = None
    consulta1.valor_pago = 0
    consulta1.forma_pagamento = ''
    consulta1.observacoes_gerais = ''
    consulta1.save()
    
    consulta1.agendamento.status = 'agendado'
    consulta1.agendamento.save()
    
    print(f"✅ Consulta {consulta1.id} ({consulta1.cliente.nome}): AGENDADA")
    print("   → Pode ser INICIADA")
    
    # Consulta 2: Em andamento (para testar finalizar)
    if len(consultas) > 1:
        consulta2 = consultas[1]
        consulta2.status = 'em_andamento'
        consulta2.data_inicio = timezone.now()
        consulta2.data_fim = None
        consulta2.valor_pago = 0
        consulta2.forma_pagamento = ''
        consulta2.observacoes_gerais = ''
        consulta2.save()
        
        consulta2.agendamento.status = 'confirmado'
        consulta2.agendamento.save()
        
        print(f"✅ Consulta {consulta2.id} ({consulta2.cliente.nome}): EM ANDAMENTO")
        print("   → Pode ser FINALIZADA")
    
    # Consulta 3: Concluída (para testar evolução)
    if len(consultas) > 2:
        consulta3 = consultas[2]
        consulta3.status = 'concluida'
        consulta3.data_inicio = timezone.now()
        consulta3.data_fim = timezone.now()
        consulta3.valor_pago = consulta3.valor_consulta
        consulta3.forma_pagamento = 'dinheiro'
        consulta3.observacoes_gerais = 'Consulta de teste concluída'
        consulta3.save()
        
        consulta3.agendamento.status = 'concluido'
        consulta3.agendamento.save()
        
        print(f"✅ Consulta {consulta3.id} ({consulta3.cliente.nome}): CONCLUÍDA")
        print("   → Pode registrar EVOLUÇÃO")

def listar_status_consultas():
    """Lista o status atual de todas as consultas"""
    print("\n📊 Status Atual das Consultas")
    print("=" * 30)
    
    consultas = Consulta.objects.all().order_by('id')
    
    for consulta in consultas:
        status_emoji = {
            'agendada': '📅',
            'em_andamento': '⏳',
            'concluida': '✅',
            'cancelada': '❌'
        }.get(consulta.status, '❓')
        
        print(f"{status_emoji} ID {consulta.id}: {consulta.cliente.nome} - {consulta.status.upper()}")

def main():
    print("🏥 Preparação de Consultas para Teste Completo")
    print("=" * 50)
    
    preparar_consultas_teste()
    listar_status_consultas()
    
    print("\n🎯 Teste Manual Agora:")
    print("1. Acesse: https://lwksistemas.com.br/loja/felix")
    print("2. Login: felipe / g$uR1t@!")
    print("3. Sistema de Consultas")
    print("4. Teste cada consulta:")
    print("   📅 Consulta AGENDADA → Botão 'Iniciar'")
    print("   ⏳ Consulta EM ANDAMENTO → Botão 'Finalizar'")
    print("   ✅ Consulta CONCLUÍDA → Registrar Evolução")

if __name__ == "__main__":
    main()