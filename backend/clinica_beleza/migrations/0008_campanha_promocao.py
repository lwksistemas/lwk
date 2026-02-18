# Campanhas de promoções (envio em massa WhatsApp)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_beleza', '0007_patient_phone_optional'),
    ]

    operations = [
        migrations.CreateModel(
            name='CampanhaPromocao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.PositiveIntegerField(db_index=True, editable=False, null=True)),
                ('titulo', models.CharField(max_length=200, verbose_name='Título da campanha')),
                ('mensagem', models.TextField(verbose_name='Mensagem (enviada por WhatsApp)')),
                ('data_inicio', models.DateField(blank=True, null=True, verbose_name='Vigência início')),
                ('data_fim', models.DateField(blank=True, null=True, verbose_name='Vigência fim')),
                ('ativa', models.BooleanField(default=True, verbose_name='Ativa')),
                ('enviada_em', models.DateTimeField(blank=True, null=True, verbose_name='Enviada em')),
                ('total_enviados', models.PositiveIntegerField(default=0, verbose_name='Total de mensagens enviadas')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
            ],
            options={
                'verbose_name': 'Campanha de promoção',
                'verbose_name_plural': 'Campanhas de promoções',
                'ordering': ['-created_at'],
                'app_label': 'clinica_beleza',
            },
        ),
    ]
