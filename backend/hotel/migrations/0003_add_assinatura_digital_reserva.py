"""
Adiciona sistema de assinatura digital para reservas de hotel:
- Campos de assinatura na Reserva (status_assinatura, conteudo_confirmacao, nomes)
- Modelo ReservaTemplate (templates de confirmação)
- Modelo ReservaAssinatura (registro de assinatura digital)
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hotel', '0002_add_funcionario'),
    ]

    operations = [
        # 1. Campos de assinatura na Reserva
        migrations.AddField(
            model_name='reserva',
            name='status_assinatura',
            field=models.CharField(
                choices=[
                    ('rascunho', 'Rascunho'),
                    ('aguardando_hospede', 'Aguardando Hóspede'),
                    ('aguardando_funcionario', 'Aguardando Funcionário'),
                    ('concluido', 'Concluído'),
                ],
                default='rascunho',
                max_length=25,
            ),
        ),
        migrations.AddField(
            model_name='reserva',
            name='conteudo_confirmacao',
            field=models.TextField(blank=True, default='', help_text='Texto da confirmação enviada ao hóspede'),
        ),
        migrations.AddField(
            model_name='reserva',
            name='nome_hospede_assinatura',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
        migrations.AddField(
            model_name='reserva',
            name='nome_funcionario_assinatura',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
        # 2. ReservaTemplate
        migrations.CreateModel(
            name='ReservaTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.IntegerField(db_index=True)),
                ('nome', models.CharField(max_length=200)),
                ('conteudo', models.TextField(help_text='Texto da confirmação. Use {hospede}, {quarto}, {checkin}, {checkout}, {valor_total}, {diarias} como variáveis.')),
                ('is_padrao', models.BooleanField(default=False)),
                ('ativo', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'hotel_reserva_templates',
                'ordering': ['-is_padrao', 'nome'],
            },
        ),
        migrations.AddIndex(
            model_name='reservatemplate',
            index=models.Index(fields=['loja_id', 'ativo'], name='hotel_restpl_loja_act_idx'),
        ),
        # 3. ReservaAssinatura
        migrations.CreateModel(
            name='ReservaAssinatura',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.IntegerField(db_index=True)),
                ('tipo', models.CharField(choices=[('hospede', 'Hóspede'), ('funcionario', 'Funcionário')], max_length=15)),
                ('nome_assinante', models.CharField(max_length=200)),
                ('email_assinante', models.EmailField(max_length=254)),
                ('ip_address', models.GenericIPAddressField(default='0.0.0.0')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('user_agent', models.TextField(blank=True, default='')),
                ('token', models.CharField(db_index=True, max_length=255, unique=True)),
                ('token_expira_em', models.DateTimeField()),
                ('assinado', models.BooleanField(default=False)),
                ('assinado_em', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('reserva', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assinaturas', to='hotel.reserva')),
            ],
            options={
                'db_table': 'hotel_reserva_assinaturas',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='reservaassinatura',
            index=models.Index(fields=['loja_id', 'token'], name='hotel_rassin_loja_tok_idx'),
        ),
        migrations.AddIndex(
            model_name='reservaassinatura',
            index=models.Index(fields=['reserva', 'tipo'], name='hotel_rassin_res_tipo_idx'),
        ),
    ]
