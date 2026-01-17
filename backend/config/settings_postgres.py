"""
Settings para produção com PostgreSQL
Implementa arquitetura de 3 bancos isolados usando schemas
"""
from .settings import *
import dj_database_url
import os

# Sobrescrever configuração de bancos para usar PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Configuração do PostgreSQL com 3 schemas isolados
    default_db = dj_database_url.config(default=DATABASE_URL, conn_max_age=600)
    
    DATABASES = {
        # BANCO 1: SuperAdmin (schema public)
        'default': {
            **default_db,
            'OPTIONS': {
                'options': '-c search_path=public'
            }
        },
        
        # BANCO 2: Suporte (schema suporte)
        'suporte': {
            **default_db,
            'OPTIONS': {
                'options': '-c search_path=suporte,public'
            }
        },
        
        # BANCO 3: Template para lojas (schema loja_template)
        'loja_template': {
            **default_db,
            'OPTIONS': {
                'options': '-c search_path=loja_template,public'
            }
        },
    }
    
    # Adicionar bancos das lojas existentes
    for loja_slug in ['felix', 'harmonis', 'loja-tech', 'moda-store']:
        DATABASES[f'loja_{loja_slug}'] = {
            **default_db,
            'OPTIONS': {
                'options': f'-c search_path=loja_{loja_slug},public'
            }
        }

# Manter o router
DATABASE_ROUTERS = ['config.db_router.MultiTenantRouter']

print("✅ PostgreSQL configurado com 3 schemas isolados")
print(f"   - default (public)")
print(f"   - suporte")
print(f"   - lojas (schemas individuais)")
