#!/usr/bin/env python
"""
Script para criar dados de exemplo para clínica de estética
"""
import os
import sys
import django
from datetime import date, time, timedelta
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clinica_estetica.models import (
    Cliente, Profissional, Procedimento, Agendamento, Funcionario,
    ProtocoloProcedimento, HorarioFuncionamento, AnamnesesTemplate
)


def criar_dados_exemplo():
    print("🏥 Criando dados de exemplo para Clínica de Estética...")
    
    # 1. Criar Profissionais
    profissionais_data = [
        {
            'nome': 'Dra. Ana Silva',
            'email': 'ana.silva@clinica.com',
            'telefone': '(11) 99999-1111',
            'especialidade': 'Dermatologia Estética',
            'registro_profissional': 'CRM 123456'
        },
        {
            'nome': 'Dra. Maria Santos',
            'email': 'maria.santos@clinica.com',
            'telefone': '(11) 99999-2222',
            'especialidade': 'Fisioterapia Dermatofuncional',
            'registro_profissional': 'CREFITO 789012'
        }
    ]
    
    profissionais = []
    for data in profissionais_data:
        prof, created = Profissional.objects.get_or_create(
            email=data['email'],
            defaults=data
        )
        profissionais.append(prof)
        print(f"✅ Profissional: {prof.nome}")
    
    # 2. Criar Procedimentos
    procedimentos_data = [
        {
            'nome': 'Limpeza de Pele Profunda',
            'descricao': 'Limpeza completa com extração e hidratação',
            'duracao': 90,
            'preco': Decimal('120.00'),
            'categoria': 'Facial'
        },
        {
            'nome': 'Peeling Químico',
            'descricao': 'Renovação celular com ácidos',
            'duracao': 60,
            'preco': Decimal('200.00'),
            'categoria': 'Facial'
        },
        {
            'nome': 'Drenagem Linfática',
            'descricao': 'Massagem para redução de inchaço',
            'duracao': 60,
            'preco': Decimal('80.00'),
            'categoria': 'Corporal'
        },
        {
            'nome': 'Radiofrequência Facial',
            'descricao': 'Tratamento para flacidez facial',
            'duracao': 45,
            'preco': Decimal('150.00'),
            'categoria': 'Facial'
        }
    ]
    
    procedimentos = []
    for data in procedimentos_data:
        proc, created = Procedimento.objects.get_or_create(
            nome=data['nome'],
            defaults=data
        )
        procedimentos.append(proc)
        print(f"✅ Procedimento: {proc.nome}")
    
    # 3. Criar Protocolos
    protocolos_data = [
        {
            'procedimento': procedimentos[0],  # Limpeza de Pele
            'nome': 'Protocolo Padrão Limpeza',
            'descricao': 'Protocolo completo para limpeza de pele profunda',
            'preparacao': '1. Higienizar as mãos\n2. Preparar materiais\n3. Acomodar cliente',
            'execucao': '1. Demaquilagem\n2. Esfoliação\n3. Vapor\n4. Extração\n5. Máscara calmante',
            'pos_procedimento': '1. Aplicar protetor solar\n2. Orientações de cuidados\n3. Agendar retorno',
            'tempo_estimado': 90,
            'materiais_necessarios': 'Demaquilante, esfoliante, vaporizador, extrator, máscara calmante, protetor solar',
            'contraindicacoes': 'Pele com lesões ativas, uso de ácidos recente',
            'cuidados_especiais': 'Evitar exposição solar por 24h'
        }
    ]
    
    for data in protocolos_data:
        protocolo, created = ProtocoloProcedimento.objects.get_or_create(
            procedimento=data['procedimento'],
            nome=data['nome'],
            defaults=data
        )
        print(f"✅ Protocolo: {protocolo.nome}")
    
    # 4. Criar Horários de Funcionamento
    horarios_data = [
        {'dia_semana': 0, 'horario_abertura': time(8, 0), 'horario_fechamento': time(18, 0), 'intervalo_inicio': time(12, 0), 'intervalo_fim': time(13, 0)},
        {'dia_semana': 1, 'horario_abertura': time(8, 0), 'horario_fechamento': time(18, 0), 'intervalo_inicio': time(12, 0), 'intervalo_fim': time(13, 0)},
        {'dia_semana': 2, 'horario_abertura': time(8, 0), 'horario_fechamento': time(18, 0), 'intervalo_inicio': time(12, 0), 'intervalo_fim': time(13, 0)},
        {'dia_semana': 3, 'horario_abertura': time(8, 0), 'horario_fechamento': time(18, 0), 'intervalo_inicio': time(12, 0), 'intervalo_fim': time(13, 0)},
        {'dia_semana': 4, 'horario_abertura': time(8, 0), 'horario_fechamento': time(18, 0), 'intervalo_inicio': time(12, 0), 'intervalo_fim': time(13, 0)},
        {'dia_semana': 5, 'horario_abertura': time(8, 0), 'horario_fechamento': time(14, 0)},  # Sábado meio período
    ]
    
    for data in horarios_data:
        horario, created = HorarioFuncionamento.objects.get_or_create(
            dia_semana=data['dia_semana'],
            defaults=data
        )
        print(f"✅ Horário: {horario}")
    
    # 5. Criar Template de Anamnese
    template_anamnese = {
        'nome': 'Anamnese Facial Completa',
        'procedimento': procedimentos[0],  # Limpeza de Pele
        'perguntas': [
            {
                'id': 1,
                'pergunta': 'Qual seu tipo de pele?',
                'tipo': 'multipla_escolha',
                'opcoes': ['Oleosa', 'Seca', 'Mista', 'Normal', 'Sensível']
            },
            {
                'id': 2,
                'pergunta': 'Tem alguma alergia conhecida?',
                'tipo': 'texto',
                'obrigatoria': True
            },
            {
                'id': 3,
                'pergunta': 'Usa algum medicamento atualmente?',
                'tipo': 'texto',
                'obrigatoria': True
            },
            {
                'id': 4,
                'pergunta': 'Já fez algum procedimento estético facial?',
                'tipo': 'sim_nao'
            },
            {
                'id': 5,
                'pergunta': 'Usa protetor solar diariamente?',
                'tipo': 'sim_nao'
            }
        ]
    }
    
    template, created = AnamnesesTemplate.objects.get_or_create(
        nome=template_anamnese['nome'],
        procedimento=template_anamnese['procedimento'],
        defaults=template_anamnese
    )
    print(f"✅ Template Anamnese: {template.nome}")
    
    # 6. Criar Clientes de Exemplo
    clientes_data = [
        {
            'nome': 'Maria da Silva',
            'email': 'maria@email.com',
            'telefone': '(11) 98888-1111',
            'cpf': '123.456.789-01',
            'data_nascimento': date(1985, 5, 15),
            'cidade': 'São Paulo',
            'estado': 'SP'
        },
        {
            'nome': 'Ana Costa',
            'email': 'ana@email.com',
            'telefone': '(11) 98888-2222',
            'cpf': '987.654.321-09',
            'data_nascimento': date(1990, 8, 22),
            'cidade': 'São Paulo',
            'estado': 'SP'
        }
    ]
    
    clientes = []
    for data in clientes_data:
        cliente, created = Cliente.objects.get_or_create(
            email=data['email'],
            defaults=data
        )
        clientes.append(cliente)
        print(f"✅ Cliente: {cliente.nome}")
    
    # 7. Criar Funcionários
    funcionarios_data = [
        {
            'nome': 'Carla Recepção',
            'email': 'carla@clinica.com',
            'telefone': '(11) 99999-3333',
            'cargo': 'Recepcionista'
        }
    ]
    
    for data in funcionarios_data:
        funcionario, created = Funcionario.objects.get_or_create(
            email=data['email'],
            defaults=data
        )
        print(f"✅ Funcionário: {funcionario.nome}")
    
    print("\n🎉 Dados de exemplo criados com sucesso!")
    print("\n📊 Resumo:")
    print(f"   👥 Profissionais: {Profissional.objects.count()}")
    print(f"   💆 Procedimentos: {Procedimento.objects.count()}")
    print(f"   📋 Protocolos: {ProtocoloProcedimento.objects.count()}")
    print(f"   🕐 Horários: {HorarioFuncionamento.objects.count()}")
    print(f"   📝 Templates Anamnese: {AnamnesesTemplate.objects.count()}")
    print(f"   👤 Clientes: {Cliente.objects.count()}")
    print(f"   👨‍💼 Funcionários: {Funcionario.objects.count()}")


if __name__ == '__main__':
    criar_dados_exemplo()