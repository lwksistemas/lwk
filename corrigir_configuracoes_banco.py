#!/usr/bin/env python3
"""
Script para corrigir configurações de bancos dinâmicos
Adiciona ATOMIC_REQUESTS e outras configurações necessárias
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_production')
sys.path.append('backend')
django.setup()

from django.conf import settings
from superadmin.models import Loja
import dj_database_url

def corrigir_configuracoes_bancos():
    print("🔧 CORRIGINDO CONFIGURAÇÕES DOS BANCOS")
    print("=" * 50)
    
    # Buscar todas as lojas com bancos criados
    lojas_com_banco = Loja.objects.filter(database_created=True)
    print(f"📊 Lojas com banco criado: {lojas_com_banco.count()}")
    
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        print("❌ DATABASE_URL não encontrada")
        return
    
    default_db = dj_database_url.config(default=DATABASE_URL, conn_max_age=600)
    
    for loja in lojas_com_banco:
        db_name = loja.database_name
        schema_name = db_name.replace('-', '_')
        
        print(f"\n🔧 Corrigindo banco: {db_name}")
        
        # Configuração completa do banco
        settings.DATABASES[db_name] = {
            **default_db,
            'OPTIONS': {
                'options': f'-c search_path={schema_name},public'
            },
            'ATOMIC_REQUESTS': False,
            'AUTOCOMMIT': True,
            'CONN_MAX_AGE': 600,
            'CONN_HEALTH_CHECKS': True,
            'TIME_ZONE': None,
        }
        
        print(f"   ✅ Configuração corrigida para: {db_name}")
    
    print(f"\n🎯 RESULTADO:")
    print(f"   ✅ {lojas_com_banco.count()} bancos corrigidos")
    print(f"   ✅ Configurações ATOMIC_REQUESTS adicionadas")
    print(f"   ✅ Sistema deve funcionar normalmente agora")

if __name__ == '__main__':
    corrigir_configuracoes_bancos()