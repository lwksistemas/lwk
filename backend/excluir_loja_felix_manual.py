#!/usr/bin/env python
"""
Script para excluir manualmente a loja felix-5889
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from superadmin.models import Loja
from django.db import transaction
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Buscar loja
    loja = Loja.objects.get(slug='felix-5889')
    
    print(f'📋 Loja encontrada:')
    print(f'  ID: {loja.id}')
    print(f'  Nome: {loja.nome}')
    print(f'  Slug: {loja.slug}')
    print(f'  Owner: {loja.owner.username}')
    print(f'  Database: {loja.database_name}')
    
    # Excluir loja (signals serão disparados automaticamente)
    print(f'\n🗑️  Excluindo loja...')
    
    with transaction.atomic():
        loja.delete()
    
    print(f'✅ Loja excluída com sucesso!')
    
except Loja.DoesNotExist:
    print(f'✅ Loja felix-5889 não existe (já foi excluída)')
    
except Exception as e:
    print(f'❌ Erro ao excluir loja: {e}')
    import traceback
    traceback.print_exc()
