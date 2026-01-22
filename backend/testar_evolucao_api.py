#!/usr/bin/env python3
"""
Script para testar a criação de evolução do paciente
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/home/luiz/Documents/lwksistemas/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clinica_estetica.models import Consulta, EvolucaoPaciente
from clinica_estetica.serializers import EvolucaoPacienteSerializer
from rest_framework.test import APIRequestFactory
from clinica_estetica.views import EvolucaoPacienteViewSet

def testar_dados_evolucao():
    """Testa a criação de evolução com dados similares ao frontend"""
    print("🏥 Testando Criação de Evolução")
    print("=" * 40)
    
    # Buscar uma consulta existente
    consulta = Consulta.objects.first()
    if not consulta:
        print("❌ Nenhuma consulta encontrada")
        return
    
    print(f"📋 Consulta encontrada: {consulta.cliente.nome}")
    print(f"   Cliente ID: {consulta.cliente.id}")
    print(f"   Profissional ID: {consulta.profissional.id}")
    print(f"   Consulta ID: {consulta.id}")
    
    # Dados similares ao que o frontend envia (com erro)
    dados_incorretos = {
        'queixa_principal': 'Teste de queixa principal',
        'areas_tratamento': 'Teste de áreas',
        'procedimento_realizado': 'Teste de procedimento',
        'consulta': consulta.id,
        'cliente': consulta.id,  # ERRO: deveria ser consulta.cliente.id
        'profissional': consulta.id,  # ERRO: deveria ser consulta.profissional.id
    }
    
    print("\n❌ Testando dados INCORRETOS (como o frontend está enviando):")
    print(f"   consulta: {dados_incorretos['consulta']}")
    print(f"   cliente: {dados_incorretos['cliente']} (ERRO: deveria ser {consulta.cliente.id})")
    print(f"   profissional: {dados_incorretos['profissional']} (ERRO: deveria ser {consulta.profissional.id})")
    
    # Testar serializer com dados incorretos
    serializer_incorreto = EvolucaoPacienteSerializer(data=dados_incorretos)
    if serializer_incorreto.is_valid():
        print("✅ Serializer aceita dados incorretos")
    else:
        print("❌ Serializer rejeita dados incorretos:")
        for field, errors in serializer_incorreto.errors.items():
            print(f"   {field}: {errors}")
    
    # Dados corretos
    dados_corretos = {
        'queixa_principal': 'Teste de queixa principal',
        'areas_tratamento': 'Teste de áreas',
        'procedimento_realizado': 'Teste de procedimento',
        'consulta': consulta.id,
        'cliente': consulta.cliente.id,  # CORRETO
        'profissional': consulta.profissional.id,  # CORRETO
    }
    
    print("\n✅ Testando dados CORRETOS:")
    print(f"   consulta: {dados_corretos['consulta']}")
    print(f"   cliente: {dados_corretos['cliente']}")
    print(f"   profissional: {dados_corretos['profissional']}")
    
    # Testar serializer com dados corretos
    serializer_correto = EvolucaoPacienteSerializer(data=dados_corretos)
    if serializer_correto.is_valid():
        print("✅ Serializer aceita dados corretos")
        # Criar evolução
        evolucao = serializer_correto.save()
        print(f"✅ Evolução criada: ID {evolucao.id}")
    else:
        print("❌ Serializer rejeita dados corretos:")
        for field, errors in serializer_correto.errors.items():
            print(f"   {field}: {errors}")

def main():
    print("🏥 Teste de Evolução do Paciente")
    print("=" * 35)
    
    testar_dados_evolucao()
    
    print("\n🎯 Conclusão:")
    print("O frontend está enviando IDs incorretos!")
    print("Precisa corrigir para enviar:")
    print("- cliente: consultaSelecionada.cliente_id (não consultaSelecionada.id)")
    print("- profissional: consultaSelecionada.profissional_id")

if __name__ == "__main__":
    main()