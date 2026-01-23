"""
Script para corrigir loja_id DEPOIS das migrations

IMPORTANTE: Executar DEPOIS de migrate
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import Loja
from crm_vendas.models import Lead, Cliente, Vendedor, Produto, Venda, Pipeline
from clinica_estetica.models import (
    Cliente as ClinicaCliente,
    Profissional,
    Procedimento,
    Agendamento,
    Funcionario,
    ProtocoloProcedimento,
    Consulta,
    EvolucaoPaciente
)

def corrigir_crm_vendas():
    """Corrige loja_id dos models de CRM Vendas"""
    print("\n📦 CRM VENDAS")
    print("-" * 80)
    
    # Obter lojas CRM
    lojas_crm = Loja.objects.filter(tipo_loja__nome='CRM Vendas', is_active=True)
    
    if not lojas_crm.exists():
        print("   ⚠️ Nenhuma loja CRM encontrada")
        return
    
    loja_crm = lojas_crm.first()
    print(f"   Usando loja: {loja_crm.nome} (ID: {loja_crm.id})")
    
    # Atualizar cada model
    models = [
        ('Leads', Lead),
        ('Clientes', Cliente),
        ('Vendedores', Vendedor),
        ('Produtos', Produto),
        ('Vendas', Venda),
        ('Pipeline', Pipeline),
    ]
    
    for nome, Model in models:
        # Usar all_without_filter para acessar todos os registros
        count = Model.objects.all_without_filter().filter(loja_id=1).update(loja_id=loja_crm.id)
        print(f"   ✅ {nome}: {count} registros atualizados")

def corrigir_clinica_estetica():
    """Corrige loja_id dos models de Clínica Estética"""
    print("\n💆 CLÍNICA ESTÉTICA")
    print("-" * 80)
    
    # Obter lojas de Clínica
    lojas_clinica = Loja.objects.filter(tipo_loja__nome='Clínica de Estética', is_active=True)
    
    if not lojas_clinica.exists():
        print("   ⚠️ Nenhuma loja de Clínica encontrada")
        return
    
    loja_clinica = lojas_clinica.first()
    print(f"   Usando loja: {loja_clinica.nome} (ID: {loja_clinica.id})")
    
    # Atualizar cada model
    models = [
        ('Clientes', ClinicaCliente),
        ('Profissionais', Profissional),
        ('Procedimentos', Procedimento),
        ('Agendamentos', Agendamento),
        ('Funcionários', Funcionario),
        ('Protocolos', ProtocoloProcedimento),
        ('Consultas', Consulta),
        ('Evoluções', EvolucaoPaciente),
    ]
    
    for nome, Model in models:
        try:
            count = Model.objects.all_without_filter().filter(loja_id=1).update(loja_id=loja_clinica.id)
            print(f"   ✅ {nome}: {count} registros atualizados")
        except Exception as e:
            print(f"   ⚠️ {nome}: Erro - {e}")

def main():
    print("=" * 80)
    print("🔧 CORREÇÃO DE loja_id - Atribuir lojas corretas")
    print("=" * 80)
    
    # Listar todas as lojas
    print("\n📋 Lojas disponíveis:")
    lojas = Loja.objects.filter(is_active=True)
    for loja in lojas:
        print(f"   {loja.id}. {loja.nome} ({loja.slug}) - {loja.tipo_loja.nome if loja.tipo_loja else 'Sem tipo'}")
    
    # Corrigir cada tipo de loja
    corrigir_crm_vendas()
    corrigir_clinica_estetica()
    
    print("\n" + "=" * 80)
    print("✅ CORREÇÃO CONCLUÍDA")
    print("=" * 80)
    print("\n📝 Verificar:")
    print("   - Todos os registros devem ter loja_id correto")
    print("   - Testar login e listagem de dados")
    print("\n")

if __name__ == '__main__':
    main()
