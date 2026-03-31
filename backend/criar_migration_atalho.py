#!/usr/bin/env python
"""
Script para criar migration dos campos atalho e subdomain
sem precisar do drf_spectacular instalado
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Desabilitar drf_spectacular temporariamente
import sys
from unittest.mock import MagicMock
sys.modules['drf_spectacular'] = MagicMock()
sys.modules['drf_spectacular.utils'] = MagicMock()
sys.modules['drf_spectacular.types'] = MagicMock()
sys.modules['drf_spectacular.views'] = MagicMock()

django.setup()

# Agora podemos importar e criar a migration
from django.core.management import call_command

print("✅ Criando migration para campos atalho e subdomain...")
call_command('makemigrations', 'superadmin', '--name', 'add_atalho_subdomain_fields')
print("✅ Migration criada com sucesso!")
