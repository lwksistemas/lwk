# Generated manually - código único por tipo de app (segurança/backup)

from django.db import migrations, models


# Mapeamento slug -> codigo único (imutável)
SLUG_TO_CODIGO = {
    'clinica-de-estetica': 'CLIEST',
    'clinica-da-beleza': 'CLIBEL',
    'crm-vendas': 'CRMVND',
    'e-commerce': 'ECOMM',
    'ecommerce': 'ECOMM',
    'restaurante': 'REST',
    'servicos': 'SERV',
    'cabeleireiro': 'CABEL',
    'clinica-estetica': 'CLIEST',  # slug alternativo
}


def populate_codigo(apps, schema_editor):
    TipoLoja = apps.get_model('superadmin', 'TipoLoja')
    for tipo in TipoLoja.objects.all():
        codigo = SLUG_TO_CODIGO.get((tipo.slug or '').strip())
        if codigo:
            tipo.codigo = codigo
            tipo.save(update_fields=['codigo'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0030_add_backup_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='tipoloja',
            name='codigo',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='Código único do tipo (ex: CLIEST, CABEL). Usado em backup e isolamento de dados.',
                max_length=20,
                null=True,
                unique=True,
            ),
        ),
        migrations.RunPython(populate_codigo, noop),
        migrations.AlterField(
            model_name='tipoloja',
            name='codigo',
            field=models.CharField(
                blank=True,
                db_index=True,
                default='',
                help_text='Código único do tipo (ex: CLIEST, CABEL). Usado em backup e isolamento de dados.',
                max_length=20,
                unique=True,
            ),
        ),
    ]
