# Generated manually for assinatura digital system

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0023_add_assinatura_fields'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        # Adicionar campo status_assinatura em Proposta
        migrations.AddField(
            model_name='proposta',
            name='status_assinatura',
            field=models.CharField(
                choices=[
                    ('rascunho', 'Rascunho'),
                    ('aguardando_cliente', 'Aguardando Cliente'),
                    ('aguardando_vendedor', 'Aguardando Vendedor'),
                    ('concluido', 'Concluído'),
                    ('cancelado', 'Cancelado'),
                ],
                default='rascunho',
                help_text='Status do processo de assinatura digital',
                max_length=20,
            ),
        ),
        # Adicionar campo status_assinatura em Contrato
        migrations.AddField(
            model_name='contrato',
            name='status_assinatura',
            field=models.CharField(
                choices=[
                    ('rascunho', 'Rascunho'),
                    ('aguardando_cliente', 'Aguardando Cliente'),
                    ('aguardando_vendedor', 'Aguardando Vendedor'),
                    ('concluido', 'Concluído'),
                    ('cancelado', 'Cancelado'),
                ],
                default='rascunho',
                help_text='Status do processo de assinatura digital',
                max_length=20,
            ),
        ),
        # Criar modelo AssinaturaDigital
        migrations.CreateModel(
            name='AssinaturaDigital',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.IntegerField(db_index=True)),
                ('object_id', models.PositiveIntegerField()),
                ('tipo', models.CharField(choices=[('cliente', 'Cliente'), ('vendedor', 'Vendedor')], help_text='Tipo de assinante', max_length=10)),
                ('nome_assinante', models.CharField(help_text='Nome completo do assinante', max_length=200)),
                ('email_assinante', models.EmailField(help_text='Email do assinante', max_length=254)),
                ('ip_address', models.GenericIPAddressField(help_text='Endereço IP do assinante')),
                ('timestamp', models.DateTimeField(auto_now_add=True, help_text='Data/hora de criação do token')),
                ('user_agent', models.TextField(blank=True, help_text='User agent do navegador')),
                ('token', models.CharField(db_index=True, help_text='Token único de assinatura', max_length=255, unique=True)),
                ('token_expira_em', models.DateTimeField(help_text='Data/hora de expiração do token')),
                ('assinado', models.BooleanField(default=False, help_text='Se o documento foi assinado')),
                ('assinado_em', models.DateTimeField(blank=True, help_text='Data/hora da assinatura', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
            ],
            options={
                'verbose_name': 'Assinatura Digital',
                'verbose_name_plural': 'Assinaturas Digitais',
                'db_table': 'crm_vendas_assinatura_digital',
                'ordering': ['-created_at'],
            },
        ),
        # Adicionar índices
        migrations.AddIndex(
            model_name='assinaturadigital',
            index=models.Index(fields=['loja_id', 'token'], name='crm_assin_loja_token_idx'),
        ),
        migrations.AddIndex(
            model_name='assinaturadigital',
            index=models.Index(fields=['loja_id', 'tipo', 'assinado'], name='crm_assin_loja_tipo_idx'),
        ),
        migrations.AddIndex(
            model_name='assinaturadigital',
            index=models.Index(fields=['content_type', 'object_id'], name='crm_assin_content_idx'),
        ),
    ]
