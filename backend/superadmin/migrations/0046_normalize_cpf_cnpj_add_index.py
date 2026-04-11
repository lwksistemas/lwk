# Generated manually
"""
Migration: Normaliza cpf_cnpj (remove formatação) e adiciona db_index.

1. RunPython: Remove pontos, traços e barras de todos os cpf_cnpj existentes.
2. RunPython: Preenche cpf_cnpj vazio a partir do slug (quando slug contém apenas dígitos de CPF/CNPJ).
3. AlterField: Adiciona db_index=True para performance na busca.
"""

from django.db import migrations, models


def normalizar_cpf_cnpj(apps, schema_editor):
    """Remove formatação de todos os cpf_cnpj existentes (pontos, traços, barras)."""
    Loja = apps.get_model('superadmin', 'Loja')
    atualizados = 0
    for loja in Loja.objects.exclude(cpf_cnpj=''):
        limpo = ''.join(c for c in loja.cpf_cnpj if c.isdigit())
        if limpo != loja.cpf_cnpj:
            loja.cpf_cnpj = limpo
            loja.save(update_fields=['cpf_cnpj'])
            atualizados += 1
    if atualizados:
        print(f"\n  ✅ {atualizados} cpf_cnpj normalizado(s) (formatação removida)")


def preencher_cpf_cnpj_do_slug(apps, schema_editor):
    """Preenche cpf_cnpj vazio quando o slug contém apenas dígitos de CPF (11) ou CNPJ (14)."""
    Loja = apps.get_model('superadmin', 'Loja')
    preenchidos = 0
    for loja in Loja.objects.filter(cpf_cnpj=''):
        digitos = ''.join(c for c in loja.slug if c.isdigit())
        if len(digitos) in (11, 14) and digitos == loja.slug:
            loja.cpf_cnpj = digitos
            loja.save(update_fields=['cpf_cnpj'])
            preenchidos += 1
    if preenchidos:
        print(f"\n  ✅ {preenchidos} cpf_cnpj preenchido(s) a partir do slug")


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0045_add_inscricao_municipal'),
    ]

    operations = [
        # 1. Normalizar dados existentes
        migrations.RunPython(
            normalizar_cpf_cnpj,
            reverse_code=migrations.RunPython.noop,
        ),
        # 2. Preencher cpf_cnpj vazio a partir do slug
        migrations.RunPython(
            preencher_cpf_cnpj_do_slug,
            reverse_code=migrations.RunPython.noop,
        ),
        # 3. Adicionar índice para performance
        migrations.AlterField(
            model_name='loja',
            name='cpf_cnpj',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='CPF ou CNPJ da loja (somente dígitos)',
                max_length=18,
            ),
        ),
    ]
