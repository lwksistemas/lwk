#!/usr/bin/env python3
"""
Script para criar consultas automaticamente a partir dos agendamentos existentes
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/home/luiz/Documents/lwksistemas/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clinica_estetica.models import Agendamento, Consulta

def criar_consultas_automaticamente():
    """Cria consultas para agendamentos que não possuem consulta"""
    print("🏥 Criando Consultas Automaticamente")
    print("=" * 50)
    
    # Buscar agendamentos sem consulta
    agendamentos_sem_consulta = Agendamento.objects.filter(consulta__isnull=True)
    
    print(f"📋 Encontrados {agendamentos_sem_consulta.count()} agendamentos sem consulta")
    
    consultas_criadas = 0
    
    for agendamento in agendamentos_sem_consulta:
        try:
            # Criar consulta
            consulta = Consulta.objects.create(
                agendamento=agendamento,
                cliente=agendamento.cliente,
                profissional=agendamento.profissional,
                procedimento=agendamento.procedimento,
                status='agendada' if agendamento.status == 'agendado' else 'concluida',
                valor_consulta=agendamento.valor,
                observacoes_gerais=agendamento.observacoes or ''
            )
            
            print(f"✅ Consulta criada: {consulta.cliente.nome} - {agendamento.data} {agendamento.horario}")
            consultas_criadas += 1
            
        except Exception as e:
            print(f"❌ Erro ao criar consulta para {agendamento.cliente.nome}: {e}")
    
    print(f"\n🎯 Resumo:")
    print(f"✅ {consultas_criadas} consultas criadas com sucesso")
    print(f"📊 Total de consultas no sistema: {Consulta.objects.count()}")

def listar_consultas():
    """Lista todas as consultas criadas"""
    print("\n📋 Consultas no Sistema")
    print("=" * 50)
    
    consultas = Consulta.objects.all().order_by('-created_at')
    
    for consulta in consultas:
        status_emoji = {
            'agendada': '📅',
            'em_andamento': '⏳',
            'concluida': '✅',
            'cancelada': '❌'
        }.get(consulta.status, '❓')
        
        print(f"{status_emoji} {consulta.cliente.nome}")
        print(f"   📅 {consulta.agendamento.data} {consulta.agendamento.horario}")
        print(f"   💆 {consulta.procedimento.nome}")
        print(f"   👨‍⚕️ {consulta.profissional.nome}")
        print(f"   💰 R$ {consulta.valor_consulta}")
        print(f"   📊 {consulta.total_evolucoes} evolução(ões)")
        print()

def main():
    print("🏥 Sistema de Consultas - Clínica de Estética")
    print("=" * 60)
    
    criar_consultas_automaticamente()
    listar_consultas()
    
    print("🎯 Sistema de consultas configurado com sucesso!")
    print("📱 Acesse: https://lwksistemas.com.br/loja/felix")
    print("🔑 Login: felipe / g$uR1t@!")
    print("🏥 Clique no botão 'Consultas' no dashboard")

if __name__ == "__main__":
    main()