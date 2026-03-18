# Generated manually on 2026-03-18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0021_add_proposta_template'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContratoTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.IntegerField(db_index=True, help_text='ID da loja (tenant)')),
                ('nome', models.CharField(help_text='Nome do template (ex: Contrato Padrão, Contrato Premium)', max_length=255)),
                ('conteudo', models.TextField(help_text='Conteúdo do template em texto ou HTML')),
                ('is_padrao', models.BooleanField(default=False, help_text='Template padrão usado ao criar novos contratos')),
                ('ativo', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Template de Contrato',
                'verbose_name_plural': 'Templates de Contratos',
                'db_table': 'crm_vendas_contrato_template',
                'ordering': ['-is_padrao', 'nome'],
                'indexes': [
                    models.Index(fields=['loja_id', 'ativo'], name='crm_ct_loja_ativo_idx'),
                    models.Index(fields=['loja_id', 'is_padrao'], name='crm_ct_loja_padrao_idx'),
                ],
            },
        ),
    ]
