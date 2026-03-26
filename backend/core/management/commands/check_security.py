"""
Comando para verificar segurança do sistema.

Uso:
    python manage.py check_security
    python manage.py check_security --fix  # Tenta corrigir problemas
"""
from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import models

from core.mixins import LojaIsolationMixin


class Command(BaseCommand):
    help = 'Verifica segurança multi-tenant do sistema'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Tenta corrigir problemas encontrados',
        )
    
    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("VERIFICAÇÃO DE SEGURANÇA MULTI-TENANT"))
        self.stdout.write("=" * 80)
        self.stdout.write("")
        
        issues = []
        
        # 1. Verificar modelos sem LojaIsolationMixin
        issues.extend(self.check_models_without_isolation())
        
        # 2. Verificar modelos sem índice em loja_id
        issues.extend(self.check_missing_loja_id_index())
        
        # 3. Verificar constraints unique sem loja_id
        issues.extend(self.check_unique_constraints())
        
        # Resumo
        self.stdout.write("")
        self.stdout.write("=" * 80)
        self.stdout.write("RESUMO")
        self.stdout.write("=" * 80)
        
        if not issues:
            self.stdout.write(self.style.SUCCESS("✅ Nenhum problema de segurança encontrado!"))
        else:
            self.stdout.write(self.style.ERROR(f"⚠️  {len(issues)} problemas encontrados:"))
            for issue in issues:
                self.stdout.write(f"  - {issue}")
        
        self.stdout.write("")
    
    def check_models_without_isolation(self):
        """Verifica modelos que deveriam ter LojaIsolationMixin."""
        issues = []
        
        self.stdout.write("1. Verificando modelos sem LojaIsolationMixin...")
        
        # Apps que devem ter isolamento
        loja_apps = [
            'crm_vendas', 'clinica_estetica', 'restaurante',
            'ecommerce', 'servicos', 'whatsapp'
        ]
        
        for app_label in loja_apps:
            try:
                app_config = apps.get_app_config(app_label)
                for model in app_config.get_models():
                    # Pular modelos intermediários e abstratos
                    if model._meta.auto_created or model._meta.abstract:
                        continue
                    
                    # Verificar se herda de LojaIsolationMixin
                    if not issubclass(model, LojaIsolationMixin):
                        issue = f"{app_label}.{model.__name__} não herda de LojaIsolationMixin"
                        issues.append(issue)
                        self.stdout.write(self.style.WARNING(f"  ⚠️  {issue}"))
            except LookupError:
                # App não existe
                pass
        
        if not issues:
            self.stdout.write(self.style.SUCCESS("  ✅ Todos os modelos têm isolamento"))
        
        self.stdout.write("")
        return issues
    
    def check_missing_loja_id_index(self):
        """Verifica modelos sem índice em loja_id."""
        issues = []
        
        self.stdout.write("2. Verificando índices em loja_id...")
        
        loja_apps = [
            'crm_vendas', 'clinica_estetica', 'restaurante',
            'ecommerce', 'servicos', 'whatsapp'
        ]
        
        for app_label in loja_apps:
            try:
                app_config = apps.get_app_config(app_label)
                for model in app_config.get_models():
                    if model._meta.auto_created or model._meta.abstract:
                        continue
                    
                    if not issubclass(model, LojaIsolationMixin):
                        continue
                    
                    # Verificar se tem índice em loja_id
                    has_index = False
                    for index in model._meta.indexes:
                        if 'loja_id' in index.fields:
                            has_index = True
                            break
                    
                    # Verificar se loja_id tem db_index=True
                    try:
                        field = model._meta.get_field('loja_id')
                        if field.db_index:
                            has_index = True
                    except:
                        pass
                    
                    if not has_index:
                        issue = f"{app_label}.{model.__name__} sem índice em loja_id"
                        issues.append(issue)
                        self.stdout.write(self.style.WARNING(f"  ⚠️  {issue}"))
            except LookupError:
                pass
        
        if not issues:
            self.stdout.write(self.style.SUCCESS("  ✅ Todos os modelos têm índice em loja_id"))
        
        self.stdout.write("")
        return issues
    
    def check_unique_constraints(self):
        """Verifica constraints unique que deveriam incluir loja_id."""
        issues = []
        
        self.stdout.write("3. Verificando constraints unique...")
        
        loja_apps = [
            'crm_vendas', 'clinica_estetica', 'restaurante',
            'ecommerce', 'servicos', 'whatsapp'
        ]
        
        for app_label in loja_apps:
            try:
                app_config = apps.get_app_config(app_label)
                for model in app_config.get_models():
                    if model._meta.auto_created or model._meta.abstract:
                        continue
                    
                    if not issubclass(model, LojaIsolationMixin):
                        continue
                    
                    # Verificar campos unique
                    for field in model._meta.fields:
                        if field.unique and field.name != 'loja_id':
                            issue = (
                                f"{app_label}.{model.__name__}.{field.name} "
                                f"é unique mas deveria ser unique_together com loja_id"
                            )
                            issues.append(issue)
                            self.stdout.write(self.style.WARNING(f"  ⚠️  {issue}"))
            except LookupError:
                pass
        
        if not issues:
            self.stdout.write(self.style.SUCCESS("  ✅ Constraints unique estão corretos"))
        
        self.stdout.write("")
        return issues
