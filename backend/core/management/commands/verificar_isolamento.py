"""
Comando para verificar isolamento de segurança entre lojas

Uso:
    python manage.py verificar_isolamento
"""

from django.core.management.base import BaseCommand
from django.apps import apps
from core.mixins import LojaIsolationMixin, LojaIsolationManager


class Command(BaseCommand):
    help = 'Verifica se todos os modelos com loja_id usam isolamento correto'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("🔒 VERIFICAÇÃO DE ISOLAMENTO DE SEGURANÇA"))
        self.stdout.write("=" * 80)
        self.stdout.write("")
        
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
        self.stdout.write(f"📊 RESUMO:")
        self.stdout.write(f"   - Modelos com isolamento correto: {len(modelos_ok)}")
        self.stdout.write(f"   - Modelos sem loja_id: {len(modelos_sem_loja)}")
        self.stdout.write(f"   - Problemas encontrados: {len(problemas)}")
        self.stdout.write("")
        
        if modelos_ok:
            self.stdout.write(self.style.SUCCESS("✅ MODELOS COM ISOLAMENTO CORRETO:"))
            for m in sorted(modelos_ok):
                self.stdout.write(f"   ✓ {m}")
            self.stdout.write("")
        
        if problemas:
            self.stdout.write(self.style.ERROR("🚨 PROBLEMAS DE SEGURANÇA ENCONTRADOS:"))
            for p in problemas:
                self.stdout.write(self.style.ERROR(f"   ❌ {p['model']}"))
                self.stdout.write(f"      {p['problema']} ({p['severidade']})")
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("⚠️  AÇÃO NECESSÁRIA: Corrigir os modelos acima!"))
        else:
            self.stdout.write(self.style.SUCCESS("✅ TODOS OS MODELOS ESTÃO CORRETAMENTE ISOLADOS!"))
