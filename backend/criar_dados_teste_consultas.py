#!/usr/bin/env python3
"""
Script para criar dados de teste para o sistema de consultas
"""

import os
import sys
import django
from datetime import date, time, datetime, timedelta

# Configurar Django
sys.path.append('/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_production')
django.setup()

from clinica_estetica.models import Cliente, Profissional, Procedimento, Agendamento, Consulta, EvolucaoPaciente

def criar_dados_teste():
    """Cria dados de teste para demonstrar o sistema de consultas"""
    print("🏥 Criando Dados de Teste - Sistema de Consultas")
    print("=" * 60)
    
    # Verificar se já existem dados
    if Cliente.objects.count() == 0:
        print("📝 Criando clientes de teste...")
        clientes = [
            Cliente.objects.create(
                nome="Maria Silva",
                email="maria.silva@email.com",
                telefone="(11) 99999-1111",
                cpf="123.456.789-01",
                data_nascimento="1985-03-15",
                endereco="Rua das Flores, 123",
                cidade="São Paulo",
                estado="SP"
            ),
            Cliente.objects.create(
                nome="Ana Santos",
                email="ana.santos@email.com",
                telefone="(11) 99999-2222",
                cpf="987.654.321-09",
                data_nascimento="1990-07-22",
                endereco="Av. Paulista, 456",
                cidade="São Paulo",
                estado="SP"
            ),
            Cliente.objects.create(
                nome="Carla Oliveira",
                email="carla.oliveira@email.com",
                telefone="(11) 99999-3333",
                data_nascimento="1988-12-10",
                endereco="Rua Augusta, 789",
                cidade="São Paulo",
                estado="SP"
            )
        ]
        print(f"✅ {len(clientes)} clientes criados")
    else:
        clientes = list(Cliente.objects.all()[:3])
        print(f"✅ Usando {len(clientes)} clientes existentes")
    
    # Verificar profissionais
    if Profissional.objects.count() == 0:
        print("👨‍⚕️ Criando profissionais de teste...")
        profissionais = [
            Profissional.objects.create(
                nome="Dra. Patricia Lima",
                email="patricia@clinica.com",
                telefone="(11) 98888-1111",
                especialidade="Dermatologista",
                registro_profissional="CRM 12345"
            ),
            Profissional.objects.create(
                nome="Esteticista Juliana",
                email="juliana@clinica.com",
                telefone="(11) 98888-2222",
                especialidade="Esteticista",
                registro_profissional="CREF 54321"
            )
        ]
        print(f"✅ {len(profissionais)} profissionais criados")
    else:
        profissionais = list(Profissional.objects.all()[:2])
        print(f"✅ Usando {len(profissionais)} profissionais existentes")
    
    # Verificar procedimentos
    if Procedimento.objects.count() == 0:
        print("💆 Criando procedimentos de teste...")
        procedimentos = [
            Procedimento.objects.create(
                nome="Limpeza de Pele Profunda",
                descricao="Limpeza completa com extração e hidratação",
                duracao=90,
                preco=120.00,
                categoria="Facial"
            ),
            Procedimento.objects.create(
                nome="Peeling Químico",
                descricao="Renovação celular com ácidos",
                duracao=60,
                preco=180.00,
                categoria="Facial"
            ),
            Procedimento.objects.create(
                nome="Massagem Relaxante",
                descricao="Massagem corporal para relaxamento",
                duracao=60,
                preco=100.00,
                categoria="Corporal"
            )
        ]
        print(f"✅ {len(procedimentos)} procedimentos criados")
    else:
        procedimentos = list(Procedimento.objects.all()[:3])
        print(f"✅ Usando {len(procedimentos)} procedimentos existentes")
    
    # Criar agendamentos e consultas
    print("📅 Criando agendamentos e consultas...")
    
    hoje = date.today()
    ontem = hoje - timedelta(days=1)
    amanha = hoje + timedelta(days=1)
    
    agendamentos_dados = [
        # Consulta concluída (ontem)
        {
            'cliente': clientes[0],
            'profissional': profissionais[0],
            'procedimento': procedimentos[0],
            'data': ontem,
            'horario': time(14, 0),
            'status': 'concluido',
            'valor': 120.00,
            'consulta_status': 'concluida'
        },
        # Consulta em andamento (hoje)
        {
            'cliente': clientes[1],
            'profissional': profissionais[1],
            'procedimento': procedimentos[1],
            'data': hoje,
            'horario': time(10, 30),
            'status': 'confirmado',
            'valor': 180.00,
            'consulta_status': 'em_andamento'
        },
        # Consulta agendada (hoje)
        {
            'cliente': clientes[2],
            'profissional': profissionais[0],
            'procedimento': procedimentos[2],
            'data': hoje,
            'horario': time(16, 0),
            'status': 'agendado',
            'valor': 100.00,
            'consulta_status': 'agendada'
        },
        # Consulta agendada (amanhã)
        {
            'cliente': clientes[0],
            'profissional': profissionais[1],
            'procedimento': procedimentos[0],
            'data': amanha,
            'horario': time(9, 0),
            'status': 'agendado',
            'valor': 120.00,
            'consulta_status': 'agendada'
        }
    ]
    
    consultas_criadas = 0
    
    for dados in agendamentos_dados:
        # Verificar se já existe
        agendamento_existente = Agendamento.objects.filter(
            cliente=dados['cliente'],
            data=dados['data'],
            horario=dados['horario']
        ).first()
        
        if not agendamento_existente:
            # Criar agendamento
            agendamento = Agendamento.objects.create(
                cliente=dados['cliente'],
                profissional=dados['profissional'],
                procedimento=dados['procedimento'],
                data=dados['data'],
                horario=dados['horario'],
                status=dados['status'],
                valor=dados['valor'],
                observacoes=f"Agendamento de teste para {dados['procedimento'].nome}"
            )
            
            # Criar consulta
            consulta = Consulta.objects.create(
                agendamento=agendamento,
                cliente=dados['cliente'],
                profissional=dados['profissional'],
                procedimento=dados['procedimento'],
                status=dados['consulta_status'],
                valor_consulta=dados['valor'],
                valor_pago=dados['valor'] if dados['consulta_status'] == 'concluida' else 0,
                forma_pagamento='cartao_credito' if dados['consulta_status'] == 'concluida' else '',
                data_inicio=datetime.combine(dados['data'], dados['horario']) if dados['consulta_status'] in ['em_andamento', 'concluida'] else None,
                data_fim=datetime.combine(dados['data'], dados['horario']) + timedelta(minutes=dados['procedimento'].duracao) if dados['consulta_status'] == 'concluida' else None
            )
            
            print(f"✅ Consulta criada: {dados['cliente'].nome} - {dados['data']} - {dados['consulta_status']}")
            consultas_criadas += 1
            
            # Criar evolução para consulta concluída
            if dados['consulta_status'] == 'concluida':
                evolucao = EvolucaoPaciente.objects.create(
                    consulta=consulta,
                    cliente=dados['cliente'],
                    agendamento=agendamento,
                    profissional=dados['profissional'],
                    queixa_principal="Deseja melhorar a aparência da pele",
                    historico_medico="Sem histórico relevante",
                    peso=65.5,
                    altura=1.65,
                    tipo_pele="mista",
                    areas_tratamento="Rosto completo",
                    procedimento_realizado=f"{dados['procedimento'].nome} realizado com sucesso. Pele limpa e hidratada.",
                    produtos_utilizados="Sabonete específico, tônico, hidratante",
                    reacao_imediata="Pele levemente avermelhada, normal após o procedimento",
                    orientacoes_dadas="Usar protetor solar, evitar exposição ao sol por 24h",
                    satisfacao_paciente=5
                )
                print(f"📊 Evolução criada para {dados['cliente'].nome}")
    
    print(f"\n🎯 Resumo dos Dados Criados:")
    print(f"👥 Clientes: {Cliente.objects.count()}")
    print(f"👨‍⚕️ Profissionais: {Profissional.objects.count()}")
    print(f"💆 Procedimentos: {Procedimento.objects.count()}")
    print(f"📅 Agendamentos: {Agendamento.objects.count()}")
    print(f"🏥 Consultas: {Consulta.objects.count()}")
    print(f"📊 Evoluções: {EvolucaoPaciente.objects.count()}")

def listar_consultas_status():
    """Lista consultas por status"""
    print("\n📋 Consultas por Status")
    print("=" * 50)
    
    status_counts = {}
    for consulta in Consulta.objects.all():
        status_counts[consulta.status] = status_counts.get(consulta.status, 0) + 1
    
    status_emojis = {
        'agendada': '📅',
        'em_andamento': '⏳',
        'concluida': '✅',
        'cancelada': '❌'
    }
    
    for status, count in status_counts.items():
        emoji = status_emojis.get(status, '❓')
        print(f"{emoji} {status.replace('_', ' ').title()}: {count}")

def main():
    criar_dados_teste()
    listar_consultas_status()
    
    print("\n🎉 Sistema de Consultas Pronto!")
    print("=" * 50)
    print("📱 Acesse: https://lwksistemas.com.br/loja/felix")
    print("🔑 Login: felipe / g$uR1t@!")
    print("🏥 Clique no botão roxo 'Consultas' no dashboard")
    print("\n📋 Funcionalidades disponíveis:")
    print("  • Visualizar todas as consultas")
    print("  • Iniciar consultas agendadas")
    print("  • Finalizar consultas em andamento")
    print("  • Registrar evolução do paciente")
    print("  • Histórico completo de evoluções")

if __name__ == "__main__":
    main()