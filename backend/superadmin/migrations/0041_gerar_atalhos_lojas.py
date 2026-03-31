# Generated manually on 2026-03-31
# ✅ NOVO v1421: Gera atalhos para lojas existentes

from django.db import migrations
from django.utils.text import slugify


def gerar_atalhos(apps, schema_editor):
    """Gera atalhos únicos para todas as lojas existentes"""
    Loja = apps.get_model('superadmin', 'Loja')
    
    for loja in Loja.objects.all():
        if not loja.atalho:
            # Gerar atalho base
            base = slugify(loja.nome)[:30].rstrip('-')
            if not base:
                base = 'loja'
            
            # Garantir unicidade
            atalho = base
            counter = 1
            while Loja.objects.filter(atalho=atalho).exclude(pk=loja.pk).exists():
                atalho = f"{base}-{counter}"
                counter += 1
            
            loja.atalho = atalho
            loja.save(update_fields=['atalho'])


def reverter_atalhos(apps, schema_editor):
    """Remove atalhos (rollback)"""
    Loja = apps.get_model('superadmin', 'Loja')
    Loja.objects.all().update(atalho='')


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0040_add_atalho_subdomain_fields'),
    ]

    operations = [
        migrations.RunPython(gerar_atalhos, reverter_atalhos),
    ]
