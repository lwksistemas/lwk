"""
Script para garantir que a configuração CRM da loja Felix tenha valores padrão.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from crm_vendas.models_config import CRMConfig
from tenants.middleware import set_current_loja_id

# Loja Felix
LOJA_ID = 1

# Definir contexto
set_current_loja_id(LOJA_ID)

# Buscar ou criar configuração
config = CRMConfig.get_or_create_for_loja(LOJA_ID)

print(f"✅ Configuração CRM para loja {LOJA_ID}")
print(f"   ID: {config.id}")
print(f"   Origens: {len(config.origens_leads)} itens")
print(f"   Etapas: {len(config.etapas_pipeline)} itens")
print(f"   Colunas: {config.colunas_leads}")
print(f"   Módulos: {config.modulos_ativos}")

# Garantir que colunas não estejam vazias
if not config.colunas_leads:
    print("\n⚠️  Colunas vazias, aplicando valores padrão...")
    config.colunas_leads = CRMConfig.get_default_colunas_leads()
    config.save()
    print(f"✅ Colunas atualizadas: {config.colunas_leads}")
else:
    print(f"\n✅ Colunas já configuradas: {config.colunas_leads}")
