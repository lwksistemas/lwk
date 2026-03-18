#!/usr/bin/env python
"""
Script para criar uma loja CRM Vendas de teste e verificar se as tabelas foram criadas.
"""
import os
import sys
import django
import json

# Configurar Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection
from superadmin.models import Loja, TipoLoja, PlanoAssinatura
from django.contrib.auth import get_user_model

User = get_user_model()

def criar_loja_teste():
    """Cria uma loja CRM Vendas de teste."""
    
    print("\n" + "="*80)
    print("CRIANDO LOJA CRM VENDAS DE TESTE")
    print("="*80)
    
    # Dados da loja
    dados_loja = {
        'cnpj': '12345678000199',
        'nome': 'Loja Teste CRM',
        'email_owner': 'teste@crm.com',
        'nome_owner': 'Teste CRM',
        'senha_owner': 'Teste@123',
        'tipo_app': 'crm-vendas',
        'plano': 'basico-crm'
    }
    
    print(f"\n📋 Dados da loja:")
    print(f"   - CNPJ: {dados_loja['cnpj']}")
    print(f"   - Nome: {dados_loja['nome']}")
    print(f"   - Email: {dados_loja['email_owner']}")
    print(f"   - Tipo: {dados_loja['tipo_app']}")
    print(f"   - Plano: {dados_loja['plano']}")
    
    try:
        # Verificar se loja já existe
        if Loja.objects.filter(slug=dados_loja['cnpj']).exists():
            print(f"\n⚠️  Loja com CNPJ {dados_loja['cnpj']} já existe")
            loja = Loja.objects.get(slug=dados_loja['cnpj'])
            print(f"   - ID: {loja.id}")
            print(f"   - Nome: {loja.nome}")
            return loja
        
        # Buscar tipo de loja
        tipo_loja = TipoLoja.objects.get(slug=dados_loja['tipo_app'])
        print(f"\n✅ Tipo de loja encontrado: {tipo_loja.nome}")
        
        # Buscar plano
        plano = PlanoAssinatura.objects.get(slug=dados_loja['plano'])
        print(f"✅ Plano encontrado: {plano.nome}")
        
        # Criar owner
        owner = User.objects.create_user(
            username=dados_loja['email_owner'].split('@')[0],
            email=dados_loja['email_owner'],
            password=dados_loja['senha_owner'],
            first_name=dados_loja['nome_owner']
        )
        print(f"✅ Owner criado: {owner.email}")
        
        # Criar loja
        loja = Loja.objects.create(
            slug=dados_loja['cnpj'],
            nome=dados_loja['nome'],
            cnpj=dados_loja['cnpj'],
            tipo_loja=tipo_loja,
            plano=plano,
            owner=owner,
            ativo=True
        )
        
        print(f"\n✅ Loja criada com sucesso!")
        print(f"   - ID: {loja.id}")
        print(f"   - Slug: {loja.slug}")
        print(f"   - Nome: {loja.nome}")
        print(f"   - Schema: loja_{loja.slug}")
        
        return loja
        
    except Exception as e:
        print(f"\n❌ Erro ao criar loja: {e}")
        import traceback
        traceback.print_exc()
        return None


def verificar_tabelas_loja(loja):
    """Verifica se as tabelas foram criadas no schema da loja."""
    
    print("\n" + "="*80)
    print("VERIFICANDO TABELAS NO SCHEMA DA LOJA")
    print("="*80)
    
    schema_name = f"loja_{loja.slug}"
    
    try:
        # Verificar se schema existe
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = %s
            """, [schema_name])
            schema_exists = cursor.fetchone()
        
        if not schema_exists:
            print(f"\n❌ Schema '{schema_name}' NÃO existe no PostgreSQL")
            return False
        
        print(f"\n✅ Schema '{schema_name}' existe no PostgreSQL")
        
        # Listar todas as tabelas no schema
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s
                ORDER BY table_name
            """, [schema_name])
            tabelas = cursor.fetchall()
        
        if not tabelas:
            print(f"\n❌ Schema '{schema_name}' está VAZIO (0 tabelas)")
            return False
        
        print(f"\n✅ Schema '{schema_name}' tem {len(tabelas)} tabelas:")
        
        # Agrupar tabelas por app
        tabelas_crm = []
        tabelas_stores = []
        tabelas_products = []
        tabelas_outras = []
        
        for (tabela,) in tabelas:
            if tabela.startswith('crm_vendas_'):
                tabelas_crm.append(tabela)
            elif tabela.startswith('stores_'):
                tabelas_stores.append(tabela)
            elif tabela.startswith('products_'):
                tabelas_products.append(tabela)
            else:
                tabelas_outras.append(tabela)
        
        # Mostrar tabelas por app
        if tabelas_crm:
            print(f"\n📊 CRM Vendas ({len(tabelas_crm)} tabelas):")
            for tabela in sorted(tabelas_crm):
                print(f"   - {tabela}")
        
        if tabelas_stores:
            print(f"\n🏪 Stores ({len(tabelas_stores)} tabelas):")
            for tabela in sorted(tabelas_stores):
                print(f"   - {tabela}")
        
        if tabelas_products:
            print(f"\n📦 Products ({len(tabelas_products)} tabelas):")
            for tabela in sorted(tabelas_products):
                print(f"   - {tabela}")
        
        if tabelas_outras:
            print(f"\n🔧 Outras ({len(tabelas_outras)} tabelas):")
            for tabela in sorted(tabelas_outras):
                print(f"   - {tabela}")
        
        # Verificar tabelas essenciais do CRM
        tabelas_essenciais_crm = [
            'crm_vendas_vendedor',
            'crm_vendas_conta',
            'crm_vendas_contato',
            'crm_vendas_lead',
            'crm_vendas_oportunidade',
            'crm_vendas_atividade'
        ]
        
        print(f"\n🔍 Verificando tabelas essenciais do CRM:")
        todas_presentes = True
        for tabela in tabelas_essenciais_crm:
            presente = tabela in [t for (t,) in tabelas]
            status = "✅" if presente else "❌"
            print(f"   {status} {tabela}")
            if not presente:
                todas_presentes = False
        
        if todas_presentes:
            print(f"\n✅ TODAS as tabelas essenciais do CRM foram criadas!")
        else:
            print(f"\n⚠️  ALGUMAS tabelas essenciais do CRM estão FALTANDO!")
        
        return todas_presentes
        
    except Exception as e:
        print(f"\n❌ Erro ao verificar tabelas: {e}")
        import traceback
        traceback.print_exc()
        return False


def verificar_search_path(loja):
    """Verifica se o search_path está configurado corretamente."""
    
    print("\n" + "="*80)
    print("VERIFICANDO SEARCH_PATH")
    print("="*80)
    
    schema_name = f"loja_{loja.slug}"
    
    try:
        from core.db_config import get_loja_database_config, ensure_loja_database_config
        
        # Garantir que o banco está configurado
        ensure_loja_database_config(schema_name, conn_max_age=60)
        
        # Conectar ao banco da loja
        from django.db import connections
        
        if schema_name not in connections:
            print(f"\n❌ Banco '{schema_name}' NÃO está em connections")
            return False
        
        print(f"\n✅ Banco '{schema_name}' está em connections")
        
        # Verificar search_path
        with connections[schema_name].cursor() as cursor:
            cursor.execute("SHOW search_path")
            search_path = cursor.fetchone()[0]
        
        print(f"\n✅ Search path: {search_path}")
        
        if schema_name in search_path:
            print(f"✅ Schema '{schema_name}' está no search_path")
            return True
        else:
            print(f"❌ Schema '{schema_name}' NÃO está no search_path")
            return False
        
    except Exception as e:
        print(f"\n❌ Erro ao verificar search_path: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    # Criar loja
    loja = criar_loja_teste()
    
    if loja:
        # Verificar tabelas
        tabelas_ok = verificar_tabelas_loja(loja)
        
        # Verificar search_path
        search_path_ok = verificar_search_path(loja)
        
        # Resumo final
        print("\n" + "="*80)
        print("RESUMO FINAL")
        print("="*80)
        print(f"Loja criada: ✅")
        print(f"Tabelas criadas: {'✅' if tabelas_ok else '❌'}")
        print(f"Search path configurado: {'✅' if search_path_ok else '❌'}")
        
        if tabelas_ok and search_path_ok:
            print(f"\n🎉 SUCESSO! Loja CRM criada e configurada corretamente!")
        else:
            print(f"\n⚠️  ATENÇÃO! Há problemas na configuração da loja.")
    else:
        print("\n❌ Falha ao criar loja")
