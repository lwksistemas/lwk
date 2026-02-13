#!/usr/bin/env python
"""
Testar carregamento individual do app clinica_beleza
"""
import os
import sys
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

print("=" * 70)
print("TESTE: Carregamento do app clinica_beleza")
print("=" * 70)

# Teste 1: Tentar carregar o app isoladamente
print("\n1. Tentando carregar app isoladamente...")
try:
    from django.apps import AppConfig
    from django.apps.registry import Apps
    
    apps_registry = Apps()
    apps_registry.populate(['clinica_beleza.apps.ClinicaBelezaConfig'])
    print("   ✅ App carregado com sucesso!")
except Exception as e:
    print(f"   ❌ Erro ao carregar app: {e}")
    traceback.print_exc()

# Teste 2: Verificar se há erro no __init__.py
print("\n2. Testando import do __init__.py...")
try:
    import clinica_beleza
    print(f"   ✅ __init__.py OK: {clinica_beleza.__file__}")
    if hasattr(clinica_beleza, 'default_app_config'):
        print(f"   - default_app_config: {clinica_beleza.default_app_config}")
except Exception as e:
    print(f"   ❌ Erro no __init__.py: {e}")
    traceback.print_exc()

# Teste 3: Verificar se há erro no apps.py
print("\n3. Testando import do apps.py...")
try:
    from clinica_beleza.apps import ClinicaBelezaConfig
    print(f"   ✅ apps.py OK")
    print(f"   - name: {ClinicaBelezaConfig.name}")
    print(f"   - verbose_name: {ClinicaBelezaConfig.verbose_name}")
    print(f"   - default_auto_field: {ClinicaBelezaConfig.default_auto_field}")
    
    # Verificar se tem método ready()
    if hasattr(ClinicaBelezaConfig, 'ready'):
        print(f"   - Tem método ready(): SIM")
    else:
        print(f"   - Tem método ready(): NÃO")
except Exception as e:
    print(f"   ❌ Erro no apps.py: {e}")
    traceback.print_exc()

# Teste 4: Comparar com cabeleireiro (que funciona)
print("\n4. Comparando com app cabeleireiro (que funciona)...")
try:
    from cabeleireiro.apps import CabeleireiroConfig
    print(f"   ✅ Cabeleireiro OK")
    print(f"   - name: {CabeleireiroConfig.name}")
    print(f"   - verbose_name: {CabeleireiroConfig.verbose_name}")
    
    if hasattr(CabeleireiroConfig, 'ready'):
        print(f"   - Tem método ready(): SIM")
    else:
        print(f"   - Tem método ready(): NÃO")
except Exception as e:
    print(f"   ❌ Erro: {e}")

# Teste 5: Tentar criar instância do AppConfig
print("\n5. Tentando criar instância do AppConfig...")
try:
    config = ClinicaBelezaConfig.create('clinica_beleza.apps.ClinicaBelezaConfig')
    print(f"   ✅ Instância criada: {config}")
    print(f"   - label: {config.label}")
    print(f"   - path: {config.path}")
except Exception as e:
    print(f"   ❌ Erro ao criar instância: {e}")
    traceback.print_exc()

print("\n" + "=" * 70)
