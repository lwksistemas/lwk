#!/usr/bin/env python
"""
Script para verificar isolamento de segurança entre lojas

Verifica se todos os modelos com loja_id estão usando:
- LojaIsolationMixin
- LojaIsolationManager

Uso:
    python manage.py shell < scripts/verificar_isolamento_seguranca.py
"""

import django
import os
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.apps import apps
from core.mixins import LojaIsolationMixin, LojaIsolationManager

def verificar_modelos():
    """Verifica se todos os modelos com loja_id usam isolamento correto"""
    print("=" * 80)
    print("🔒 VERIFICAÇÃO DE ISOLAMENTO DE SEGURANÇA")
    print("=" * 80)
    print()
    
    problemas = []
    modelos_ok = []
    modelos_sem_loja = []
    
    for model in apps.get_models():
        model_name = f"{model._meta.app_label}.{model.__name__}"
        
        # Verificar se tem campo loja_id
        has_loja_id = hasattr(model, 'loja_id')
        
        if not has_loja_id:
            modelos_sem_loja.append(model_name)
            continue
        
        # Verificar se usa LojaIsolationMixin
        uses_mixin = issubclass(model, LojaIsolationMixin)
        
        # Verificar se usa LojaIsolationManager
        uses_manager = isinstance(model.objects, LojaIsolationManager)
        
        if not uses_mixin:
            problemas.append({
                'model': model_name,
                'problema': 'Tem loja_id mas NÃO usa LojaIsolationMixin',
                'severidade': 'CRÍTICO'
            })
        
        if not uses_manager:
            problemas.append({
                'model': model_name,
                'problema': 'Tem loja_id mas NÃO usa LojaIsolationManager',
                'severidade': 'CRÍTICO'
            })
        
        if uses_mixin and uses_manager:
            modelos_ok.append(model_name)
    
    # Relatório
    print(f"📊 RESUMO:")
    print(f"   - Modelos com isolamento correto: {len(modelos_ok)}")
    print(f"   - Modelos sem loja_id: {len(modelos_sem_loja)}")
    print(f"   - Problemas encontrados: {len(problemas)}")
    print()
    
    if modelos_ok:
        print("✅ MODELOS COM ISOLAMENTO CORRETO:")
        for m in sorted(modelos_ok):
            print(f"   ✓ {m}")
        print()
    
    if problemas:
        print("🚨 PROBLEMAS DE SEGURANÇA ENCONTRADOS:")
        for p in problemas:
            print(f"   ❌ {p['model']}")
            print(f"      {p['problema']} ({p['severidade']})")
        print()
        print("⚠️  AÇÃO NECESSÁRIA: Corrigir os modelos acima!")
        return False
    else:
        print("✅ TODOS OS MODELOS ESTÃO CORRETAMENTE ISOLADOS!")
        return True

if __name__ == '__main__':
    sucesso = verificar_modelos()
    sys.exit(0 if sucesso else 1)
