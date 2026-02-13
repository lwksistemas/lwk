#!/usr/bin/env python
"""
Debug: Verificar por que clinica_beleza não está sendo carregado
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

print("=" * 70)
print("DEBUG: INSTALLED_APPS")
print("=" * 70)

# Ler o arquivo settings.py diretamente
print("\n1. Lendo settings.py diretamente...")
with open('config/settings.py', 'r') as f:
    content = f.read()
    
# Encontrar INSTALLED_APPS
start = content.find('INSTALLED_APPS = [')
end = content.find(']', start) + 1
installed_apps_str = content[start:end]

print(installed_apps_str)

# Contar apps
apps_count = installed_apps_str.count("'")
print(f"\nTotal de linhas com aspas: {apps_count}")

# Agora carregar via Django
print("\n2. Carregando via Django settings...")
from django.conf import settings
print(f"Total de apps carregados: {len(settings.INSTALLED_APPS)}")
print("\nApps carregados:")
for i, app in enumerate(settings.INSTALLED_APPS, 1):
    print(f"  {i}. {app}")

print("\n" + "=" * 70)
