#!/usr/bin/env python
"""
Forçar carregamento do app clinica_beleza e ver o erro exato
"""
import os
import sys
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

print("=" * 70)
print("FORÇANDO CARREGAMENTO DO APP CLINICA_BELEZA")
print("=" * 70)

# Importar Django
import django
from django.conf import settings

print(f"\n1. INSTALLED_APPS original tem {len(settings.INSTALLED_APPS)} apps")
print(f"   Clinica beleza está na lista: {'clinica_beleza.apps.ClinicaBelezaConfig' in settings.INSTALLED_APPS}")

# Tentar fazer setup do Django e capturar qualquer erro
print("\n2. Fazendo django.setup()...")
try:
    django.setup()
    print("   ✅ Django setup concluído")
except Exception as e:
    print(f"   ❌ Erro durante setup: {e}")
    traceback.print_exc()

# Verificar apps carregados
print("\n3. Verificando apps carregados após setup...")
from django.apps import apps
loaded_apps = [app.name for app in apps.get_app_configs()]
print(f"   Total de apps carregados: {len(loaded_apps)}")
print(f"   Clinica beleza carregado: {'clinica_beleza' in loaded_apps}")

if 'clinica_beleza' not in loaded_apps:
    print("\n   ❌ CLINICA_BELEZA NÃO FOI CARREGADO!")
    print("\n   Apps que foram carregados:")
    for app in loaded_apps:
        print(f"     - {app}")

# Tentar carregar manualmente
print("\n4. Tentando carregar clinica_beleza manualmente...")
try:
    from clinica_beleza.apps import ClinicaBelezaConfig
    config = ClinicaBelezaConfig('clinica_beleza', __import__('clinica_beleza'))
    print(f"   ✅ Config criado: {config}")
    print(f"   - name: {config.name}")
    print(f"   - label: {config.label}")
    print(f"   - path: {config.path}")
    
    # Tentar importar models
    print("\n5. Tentando importar models...")
    config.import_models()
    print(f"   ✅ Models importados")
    
except Exception as e:
    print(f"   ❌ Erro: {e}")
    traceback.print_exc()

print("\n" + "=" * 70)
