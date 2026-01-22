#!/usr/bin/env python3
"""
Script para debugar detalhadamente o problema de evolução
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/home/luiz/Documents/lwksistemas/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clinica_estetica.models import Consulta, EvolucaoPaciente, Cliente, Profissional
from clinica_estetica.serializers import EvolucaoPacienteSerializer
from rest_framework.test import APIRequestFactory
from clinica_estetica.views import EvolucaoPacienteViewSet
import json

def debug_dados_consulta():
    """Debug detalhado dos dados da consulta"""
    print("🔍 Debug Detalhado - Dados da Consulta")
    print("=" * 45)
    
    # Buscar consulta ID 2 (que aparece nos logs)
    try:
        consulta = Consulta.objects.get(id=2)
        print(f"📋 Consulta ID 2 encontrada:")
        print(f"   Cliente ID: {consulta.cliente.id}")
        print(f"   Cliente Nome: {consulta.cliente.nome}")
        print(f"   Profissional ID: {consulta.profissional.id}")
        print(f"   Profissional Nome: {consulta.profissional.nome}")
        print(f"   Status: {consulta.status}")
        
        # Verificar se cliente e profissional existem
        cliente_existe = Cliente.objects.filter(id=consulta.cliente.id).exists()
        profissional_existe = Profissional.objects.filter(id=consulta.profissional.id).exists()
        
        print(f"   Cliente existe: {cliente_existe}")
        print(f"   Profissional existe: {profissional_existe}")
        
        return consulta
        
    except Consulta.DoesNotExist:
        print("❌ Consulta ID 2 não encontrada")
        return None

def testar_dados_minimos():
    """Testa com dados mínimos obrigatórios"""
    print("\n🧪 Teste com Dados Mínimos")
    print("=" * 30)
    
    consulta = debug_dados_consulta()
    if not consulta:
        return
    
    # Dados mínimos obrigatórios
    dados_minimos = {
        'consulta': consulta.id,
        'cliente': consulta.cliente.id,
        'profissional': consulta.profissional.id,
        'queixa_principal': 'Teste de queixa principal',
        'areas_tratamento': 'Teste de áreas',
        'procedimento_realizado': 'Teste de procedimento'
    }
    
    print("📊 Dados sendo testados:")
    for key, value in dados_minimos.items():
        print(f"   {key}: {value}")
    
    # Testar serializer
    serializer = EvolucaoPacienteSerializer(data=dados_minimos)
    
    print(f"\n📋 Serializer válido: {serializer.is_valid()}")
    
    if not serializer.is_valid():
        print("❌ Erros do serializer:")
        for field, errors in serializer.errors.items():
            print(f"   {field}: {errors}")
    else:
        print("✅ Serializer aceita os dados")
        try:
            evolucao = serializer.save()
            print(f"✅ Evolução criada com ID: {evolucao.id}")
        except Exception as e:
            print(f"❌ Erro ao salvar: {e}")

def testar_dados_completos():
    """Testa com dados completos como o frontend envia"""
    print("\n🧪 Teste com Dados Completos (Frontend)")
    print("=" * 40)
    
    consulta = Consulta.objects.get(id=2)
    
    # Dados como o frontend envia
    dados_frontend = {
        'consulta': consulta.id,
        'cliente': consulta.cliente.id,
        'profissional': consulta.profissional.id,
        'queixa_principal': 'Dor nas costas',
        'historico_medico': None,
        'medicamentos_uso': None,
        'alergias': None,
        'peso': None,
        'altura': None,
        'pressao_arterial': '',
        'tipo_pele': '',
        'condicoes_pele': '',
        'areas_tratamento': 'Região lombar',
        'procedimento_realizado': 'Massagem terapêutica',
        'produtos_utilizados': '',
        'parametros_equipamento': '',
        'reacao_imediata': '',
        'orientacoes_dadas': '',
        'proxima_sessao': None,
        'satisfacao_paciente': None
    }
    
    print("📊 Dados completos sendo testados:")
    for key, value in dados_frontend.items():
        print(f"   {key}: {value}")
    
    # Testar serializer
    serializer = EvolucaoPacienteSerializer(data=dados_frontend)
    
    print(f"\n📋 Serializer válido: {serializer.is_valid()}")
    
    if not serializer.is_valid():
        print("❌ Erros do serializer:")
        for field, errors in serializer.errors.items():
            print(f"   {field}: {errors}")
    else:
        print("✅ Serializer aceita os dados completos")

def verificar_campos_obrigatorios():
    """Verifica quais campos são obrigatórios no modelo"""
    print("\n📋 Campos Obrigatórios do Modelo")
    print("=" * 35)
    
    from clinica_estetica.models import EvolucaoPaciente
    
    # Verificar campos obrigatórios
    campos_obrigatorios = []
    campos_opcionais = []
    
    for field in EvolucaoPaciente._meta.fields:
        if not field.null and not field.blank and not hasattr(field, 'auto_now_add'):
            campos_obrigatorios.append(field.name)
        else:
            campos_opcionais.append(field.name)
    
    print("✅ Campos obrigatórios:")
    for campo in campos_obrigatorios:
        print(f"   - {campo}")
    
    print("\n📝 Campos opcionais:")
    for campo in campos_opcionais[:10]:  # Mostrar apenas os primeiros 10
        print(f"   - {campo}")

def main():
    print("🏥 Debug Detalhado - Evolução do Paciente")
    print("=" * 50)
    
    verificar_campos_obrigatorios()
    debug_dados_consulta()
    testar_dados_minimos()
    testar_dados_completos()
    
    print("\n🎯 Próximos Passos:")
    print("1. Verificar se os erros são de validação de campos")
    print("2. Verificar se há problemas de foreign key")
    print("3. Testar com dados exatos do frontend")

if __name__ == "__main__":
    main()