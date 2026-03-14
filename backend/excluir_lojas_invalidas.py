#!/usr/bin/env python
"""
Script para excluir lojas com schemas vazios
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from superadmin.models import Loja
from django.db import connection

print('='*60)
print('EXCLUSÃO DE LOJAS INVÁLIDAS')
print('='*60)

# IDs das lojas com schemas vazios
lojas_invalidas = [34, 36]

for loja_id in lojas_invalidas:
    try:
        loja = Loja.objects.get(id=loja_id)
        print(f'\n🗑️  Excluindo loja ID:{loja_id} | {loja.nome} ({loja.slug})')
        
        # Verificar se schema está vazio
        schema_name = loja.database_name.replace('-', '_')
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_type = 'BASE TABLE'
            """, [schema_name])
            count = cursor.fetchone()[0]
            print(f'   Schema {schema_name}: {count} tabelas')
        
        # Excluir loja
        loja.delete()
        print(f'   ✅ Loja excluída com sucesso')
        
    except Loja.DoesNotExist:
        print(f'   ⚠️  Loja ID:{loja_id} não encontrada')
    except Exception as e:
        print(f'   ❌ Erro ao excluir loja ID:{loja_id}: {e}')

print('\n✅ Processo concluído')
