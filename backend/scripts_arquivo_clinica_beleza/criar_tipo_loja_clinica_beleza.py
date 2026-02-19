"""
Script para criar o tipo de loja "Clínica da Beleza" no sistema.
Execute a partir da pasta backend: python scripts_arquivo_clinica_beleza/criar_tipo_loja_clinica_beleza.py
"""
import os
import sys

# Garantir que backend está no path (para config.settings)
_script_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_script_dir)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from superadmin.models import TipoLoja

def criar_tipo_loja_clinica_beleza():
    print("🏥 Criando tipo de loja: Clínica da Beleza...")
    
    # Verificar se já existe
    tipo_existente = TipoLoja.objects.filter(nome="Clínica da Beleza").first()
    
    if tipo_existente:
        print(f"⚠️  Tipo de loja 'Clínica da Beleza' já existe (ID: {tipo_existente.id})")
        return tipo_existente
    
    # Criar novo tipo de loja
    tipo_loja = TipoLoja.objects.create(
        nome="Clínica da Beleza",
        slug="clinica-da-beleza",
        descricao="Sistema completo para gestão de clínicas de estética e beleza com agendamentos, procedimentos, pacientes e pagamentos",
        dashboard_template="clinica-beleza",
        cor_primaria="#EC4899",  # Rosa/Pink
        cor_secundaria="#DB2777",  # Rosa escuro
        tem_produtos=False,
        tem_servicos=True,
        tem_agendamento=True,
        tem_delivery=False,
        tem_estoque=False
    )
    
    print(f"✅ Tipo de loja 'Clínica da Beleza' criado com sucesso! (ID: {tipo_loja.id})")
    print(f"📋 Descrição: {tipo_loja.descricao}")
    
    # Listar todos os tipos de loja disponíveis
    print("\n📊 Tipos de loja disponíveis no sistema:")
    for tipo in TipoLoja.objects.all().order_by('nome'):
        print(f"   - {tipo.nome} (ID: {tipo.id}) - Slug: {tipo.slug}")
    
    return tipo_loja

if __name__ == '__main__':
    criar_tipo_loja_clinica_beleza()
