#!/usr/bin/env python3
"""
Script para testar a API de consultas diretamente
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/home/luiz/Documents/lwksistemas/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clinica_estetica.models import Consulta
from clinica_estetica.serializers import ConsultaSerializer
from clinica_estetica.views import ConsultaViewSet
from django.test import RequestFactory

def testar_consultas_diretamente():
    """Testa as consultas diretamente no modelo"""
    print("🏥 Testando Consultas - Modelo Django")
    print("=" * 50)
    
    # Testar modelo diretamente
    consultas = Consulta.objects.all()
    print(f"📊 Total de consultas no modelo: {consultas.count()}")
    
    for consulta in consultas:
        print(f"✅ ID: {consulta.id} - {consulta.cliente.nome} - Status: {consulta.status}")
    
    print("\n🔄 Testando Serializer")
    print("=" * 30)
    
    # Testar serializer
    serializer = ConsultaSerializer(consultas, many=True)
    print(f"📊 Dados serializados: {len(serializer.data)} consultas")
    
    for item in serializer.data:
        print(f"✅ ID: {item['id']} - {item['cliente_nome']} - Status: {item['status']}")
    
    print("\n🌐 Testando ViewSet")
    print("=" * 20)
    
    # Testar ViewSet
    factory = RequestFactory()
    request = factory.get('/clinica/consultas/')
    
    viewset = ConsultaViewSet()
    viewset.request = request
    
    try:
        queryset = viewset.get_queryset()
        print(f"📊 Queryset do ViewSet: {queryset.count()} consultas")
        
        for consulta in queryset:
            print(f"✅ ID: {consulta.id} - {consulta.cliente.nome} - Status: {consulta.status}")
            
    except Exception as e:
        print(f"❌ Erro no ViewSet: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🏥 Teste da API de Consultas")
    print("=" * 40)
    
    testar_consultas_diretamente()

if __name__ == "__main__":
    main()