#!/usr/bin/env python
"""
Script para reenviar PDF final da Proposta #31 (SISENANDO SOARES)
que foi assinada mas o email não foi enviado devido ao bug do threading.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from crm_vendas.models import Proposta
from crm_vendas.assinatura_digital_service import enviar_pdf_final
from superadmin.models import Loja

def main():
    # Loja: Felix Representações (41449198000172)
    loja_id = 172
    proposta_id = 31
    
    print(f"🔍 Buscando Proposta #{proposta_id} da loja {loja_id}...")
    
    # Obter loja e configurar schema
    loja = Loja.objects.using('default').get(id=loja_id)
    schema_name = loja.schema_name
    
    print(f"✅ Loja encontrada: {loja.nome} (schema: {schema_name})")
    
    # Configurar conexão com schema do tenant
    connection.set_schema(schema_name)
    
    # Buscar proposta
    try:
        proposta = Proposta.objects.select_related(
            'oportunidade',
            'oportunidade__lead',
            'oportunidade__vendedor'
        ).get(id=proposta_id)
        
        print(f"✅ Proposta encontrada: {proposta.titulo}")
        print(f"   Cliente: {proposta.oportunidade.lead.nome}")
        print(f"   Status: {proposta.status_assinatura}")
        
        if proposta.status_assinatura != 'concluido':
            print(f"⚠️  Proposta não está com status 'concluido': {proposta.status_assinatura}")
            return
        
        print(f"\n📧 Enviando PDF final...")
        
        # Enviar PDF final
        sucesso, erro = enviar_pdf_final(proposta, loja_id)
        
        if sucesso or erro is None:
            print(f"✅ PDF final enviado com sucesso!")
            print(f"   Destinatários:")
            if proposta.oportunidade.lead.email:
                print(f"   - Cliente: {proposta.oportunidade.lead.email}")
            if proposta.oportunidade.vendedor and proposta.oportunidade.vendedor.email:
                print(f"   - Vendedor: {proposta.oportunidade.vendedor.email}")
            elif loja.owner and loja.owner.email:
                print(f"   - Admin: {loja.owner.email}")
        else:
            print(f"❌ Erro ao enviar PDF: {erro}")
    
    except Proposta.DoesNotExist:
        print(f"❌ Proposta #{proposta_id} não encontrada no schema {schema_name}")
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
