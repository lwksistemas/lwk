# Recurso: assinatura digital do recibo do procedimento.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_beleza', '0082_payment_data_vencimento'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='status_assinatura_recibo',
            field=models.CharField(
                choices=[
                    ('rascunho', 'Rascunho'),
                    ('aguardando_paciente', 'Aguardando Paciente'),
                    ('concluido', 'Concluído'),
                ],
                default='rascunho',
                max_length=30,
                verbose_name='Status assinatura do recibo',
            ),
        ),
        migrations.CreateModel(
            name='ReciboAssinatura',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.IntegerField(db_index=True, help_text='ID da loja proprietária deste registro')),
                ('tipo', models.CharField(choices=[('paciente', 'Paciente')], default='paciente', max_length=15)),
                ('nome_assinante', models.CharField(max_length=200)),
                ('email_assinante', models.EmailField(blank=True, default='', max_length=254)),
                ('ip_address', models.GenericIPAddressField(default='0.0.0.0')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('user_agent', models.TextField(blank=True, default='')),
                ('token', models.CharField(db_index=True, max_length=255, unique=True)),
                ('token_expira_em', models.DateTimeField()),
                ('assinado', models.BooleanField(default=False)),
                ('assinado_em', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('payment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assinaturas_recibo', to='clinica_beleza.payment', verbose_name='Pagamento')),
            ],
            options={
                'db_table': 'clinica_beleza_recibo_assinaturas',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['loja_id', 'token'], name='cb_recibo_assin_loja_tok_idx'),
                    models.Index(fields=['payment', 'tipo'], name='cb_recibo_assin_pay_tipo_idx'),
                ],
            },
        ),
    ]
