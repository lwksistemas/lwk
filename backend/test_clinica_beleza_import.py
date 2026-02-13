#!/usr/bin/env python
"""
Script para testar o carregamento do app clinica_beleza
"""
import os
import sys
import django
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

print("=" * 60)
print("TESTE DE CARREGAMENTO DO APP CLINICA_BELEZA")
print("=" * 60)

# Teste 1: Import do módulo
print("\n1. Testando import do módulo clinica_beleza...")
try:
    import clinica_beleza
    print(f"   ✅ Módulo importado: {clinica_beleza.__file__}")
except Exception as e:
    print(f"   ❌ Erro ao importar módulo: {e}")
    traceback.print_exc()

# Teste 2: Import do apps.py
print("\n2. Testando import do ClinicaBelezaConfig...")
try:
    from clinica_beleza.apps import ClinicaBelezaConfig
    print(f"   ✅ Config importado: {ClinicaBelezaConfig.name}")
except Exception as e:
    print(f"   ❌ Erro ao importar config: {e}")
    traceback.print_exc()

# Teste 3: Import dos models
print("\n3. Testando import dos models...")
try:
    django.setup()
    from clinica_beleza import models
    print(f"   ✅ Models importados")
    print(f"   - Patient: {models.Patient}")
    print(f"   - Professional: {models.Professional}")
except Exception as e:
    print(f"   ❌ Erro ao importar models: {e}")
    traceback.print_exc()

# Teste 4: Verificar se app está registrado
print("\n4. Verificando se app está registrado no Django...")
try:
    from django.apps import apps
    all_apps = [app.name for app in apps.get_app_configs()]
    print(f"   Total de apps: {len(all_apps)}")
    print(f"   Clinica beleza registrado: {'clinica_beleza' in all_apps}")
    
    if 'clinica_beleza' not in all_apps:
        print("\n   ❌ APP NÃO REGISTRADO!")
        print(f"   Apps registrados: {all_apps}")
except Exception as e:
    print(f"   ❌ Erro: {e}")
    traceback.print_exc()

# Teste 5: Verificar INSTALLED_APPS
print("\n5. Verificando INSTALLED_APPS...")
try:
    from django.conf import settings
    installed = settings.INSTALLED_APPS
    print(f"   Total em INSTALLED_APPS: {len(installed)}")
    
    clinica_entries = [app for app in installed if 'clinica' in app.lower()]
    print(f"   Entradas com 'clinica': {clinica_entries}")
except Exception as e:
    print(f"   ❌ Erro: {e}")
    traceback.print_exc()

print("\n" + "=" * 60)
print("FIM DOS TESTES")
print("=" * 60)
