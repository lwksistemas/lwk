# AlterField: atualiza help_text (metadados, sem impacto no schema)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0017_add_indexes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='atividade',
            name='criado_por_vendedor_id',
            field=models.PositiveIntegerField(
                blank=True,
                db_index=True,
                help_text='Vendedor que criou/importou esta atividade (órfã). Null = proprietário. Usado para filtrar calendário por vendedor.',
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name='crmconfig',
            name='loja_id',
            field=models.IntegerField(
                db_index=True,
                help_text='ID da loja proprietária desta configuração',
            ),
        ),
    ]
