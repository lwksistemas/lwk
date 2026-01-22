#!/usr/bin/env python3
"""
Script para testar a evolução com a correção aplicada
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/home/luiz/Documents/lwksistemas/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clinica_estetica.models import Consulta
from clinica_estetica.serializers import EvolucaoPacienteSerializer

def testar_dados_corrigidos():
    """Testa com dados como o frontend agora envia (após correção)"""
    print("🧪 Teste com Dados Corrigidos (Frontend)")
    print("=" * 40)
    
    consulta = Consulta.objects.get(id=2)
    
    # Dados como o frontend AGORA envia (após correção)
    dados_corrigidos = {
        'consulta': consulta.id,
        'cliente': consulta.cliente.id,
        'profissional': consulta.profissional.id,
        'queixa_principal': 'Dor nas costas',
        'historico_medico': '',  # String vazia em vez de null
        'medicamentos_uso': '',  # String vazia em vez de null
        'alergias': '',          # String vazia em vez de null
        'peso': None,            # Null OK para campos numéricos
        'altura': None,          # Null OK para campos numéricos
        'pressao_arterial': '',  # String vazia
        'tipo_pele': '',         # String vazia
        'condicoes_pele': '',    # String vazia
        'areas_tratamento': 'Região lombar',
        'procedimento_realizado': 'Massagem terapêutica',
        'produtos_utilizados': '',      # String vazia
        'parametros_equipamento': '',   # String vazia
        'reacao_imediata': '',          # String vazia
        'orientacoes_dadas': '',        # String vazia
        'proxima_sessao': None,         # Null OK para data
        'satisfacao_paciente': None     # Null OK para inteiro
    }
    
    print("📊 Dados corrigidos sendo testados:")
    for key, value in dados_corrigidos.items():
        tipo = type(value).__name__
        print(f"   {key}: {value} ({tipo})")
    
    # Testar serializer
    serializer = EvolucaoPacienteSerializer(data=dados_corrigidos)
    
    print(f"\n📋 Serializer válido: {serializer.is_valid()}")
    
    if not serializer.is_valid():
        print("❌ Erros do serializer:")
        for field, errors in serializer.errors.items():
            print(f"   {field}: {errors}")
        return False
    else:
        print("✅ Serializer aceita os dados corrigidos")
        try:
            evolucao = serializer.save()
            print(f"✅ Evolução criada com ID: {evolucao.id}")
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar: {e}")
            return False

def main():
    print("🏥 Teste da Correção - Evolução do Paciente")
    print("=" * 50)
    
    sucesso = testar_dados_corrigidos()
    
    print("\n🎯 Resultado:")
    if sucesso:
        print("✅ CORREÇÃO FUNCIONOU!")
        print("✅ Frontend agora envia dados corretos")
        print("✅ Evolução pode ser registrada sem erro")
        print("\n📱 Teste manual:")
        print("1. Acesse: https://lwksistemas.com.br/loja/felix")
        print("2. Login: felipe / g$uR1t@!")
        print("3. Sistema de Consultas → Selecionar consulta")
        print("4. Evolução do Paciente → + Nova Evolução")
        print("5. Preencher e salvar - deve funcionar agora!")
    else:
        print("❌ Ainda há problemas")
        print("Verificar se há outros campos problemáticos")

if __name__ == "__main__":
    main()