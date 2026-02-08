#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings

print('🔍 Verificando MIDDLEWARE:')
print(f'\nTotal de middlewares: {len(settings.MIDDLEWARE)}')
print('\nLista completa:')
for i, mw in enumerate(settings.MIDDLEWARE, 1):
    print(f'  {i}. {mw}')
    if 'historico' in mw.lower():
        print('     ✅ ENCONTRADO!')

print('\n🔍 Procurando por "historico":')
historico_found = any('historico' in mw.lower() for mw in settings.MIDDLEWARE)
print(f'Resultado: {"✅ SIM" if historico_found else "❌ NÃO"}')
