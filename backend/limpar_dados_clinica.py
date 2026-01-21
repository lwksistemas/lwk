#!/usr/bin/env python
"""
Script para limpar dados de exemplo da clínica estética
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clinica_estetica.models import *

def limpar_dados_clinica():
    print('🧹 Removendo dados de exemplo da clínica estética...')
    
    # Contar antes
    total_antes = {
        'clientes': Cliente.objects.count(),
        'profissionais': Profissional.objects.count(),
        'procedimentos': Procedimento.objects.count(),
        'protocolos': ProtocoloProcedimento.objects.count(),
        'horarios': HorarioFuncionamento.objects.count(),
        'templates': AnamnesesTemplate.objects.count(),
        'funcionarios': Funcionario.objects.count(),
        'agendamentos': Agendamento.objects.count(),
        'evolucoes': EvolucaoPaciente.objects.count(),
        'anamneses': Anamnese.objects.count(),
        'bloqueios': BloqueioAgenda.objects.count(),
    }
    
    print('📊 Dados antes da limpeza:')
    for modelo, count in total_antes.items():
        print(f'   {modelo}: {count}')
    
    # Remover todos os dados de exemplo (ordem importante por causa das FKs)
    Anamnese.objects.all().delete()
    EvolucaoPaciente.objects.all().delete()
    Agendamento.objects.all().delete()
    ProtocoloProcedimento.objects.all().delete()
    AnamnesesTemplate.objects.all().delete()
    BloqueioAgenda.objects.all().delete()
    Cliente.objects.all().delete()
    Profissional.objects.all().delete()
    Procedimento.objects.all().delete()
    HorarioFuncionamento.objects.all().delete()
    Funcionario.objects.all().delete()
    
    # Contar depois
    total_depois = {
        'clientes': Cliente.objects.count(),
        'profissionais': Profissional.objects.count(),
        'procedimentos': Procedimento.objects.count(),
        'protocolos': ProtocoloProcedimento.objects.count(),
        'horarios': HorarioFuncionamento.objects.count(),
        'templates': AnamnesesTemplate.objects.count(),
        'funcionarios': Funcionario.objects.count(),
        'agendamentos': Agendamento.objects.count(),
        'evolucoes': EvolucaoPaciente.objects.count(),
        'anamneses': Anamnese.objects.count(),
        'bloqueios': BloqueioAgenda.objects.count(),
    }
    
    print('\n📊 Dados após a limpeza:')
    for modelo, count in total_depois.items():
        print(f'   {modelo}: {count}')
    
    print('\n✅ Todos os dados de exemplo removidos!')
    print('🎯 Dashboard da clínica agora está limpo para novas lojas')
    print('🏥 Cada nova loja de clínica estética começará com dados vazios')

if __name__ == '__main__':
    limpar_dados_clinica()