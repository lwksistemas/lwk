# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0008_add_comissao_data_fechamento_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='CRMConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.IntegerField(db_index=True)),
                ('origens_leads', models.JSONField(blank=True, default=list, help_text='Lista de origens personalizadas para leads')),
                ('etapas_pipeline', models.JSONField(blank=True, default=list, help_text='Lista de etapas personalizadas do pipeline')),
                ('colunas_leads', models.JSONField(blank=True, default=list, help_text='Colunas visíveis na listagem de leads')),
                ('modulos_ativos', models.JSONField(blank=True, default=dict, help_text='Módulos ativos no CRM')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Configuração CRM',
                'verbose_name_plural': 'Configurações CRM',
                'db_table': 'crm_vendas_config',
                'indexes': [
                    models.Index(fields=['loja_id'], name='crm_config_loja_idx'),
                ],
            },
        ),
    ]
