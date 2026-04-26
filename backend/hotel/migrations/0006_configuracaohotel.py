from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hotel', '0005_quarto_unique_numero_somente_ativo'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfiguracaoHotel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.IntegerField(db_index=True, help_text='ID da loja dona deste registro')),
                ('horario_checkin', models.TimeField(default='14:00', help_text='Horário padrão de check-in')),
                ('horario_checkout', models.TimeField(default='12:00', help_text='Horário padrão de check-out')),
                ('politica_cancelamento', models.TextField(blank=True, default='')),
                ('informacoes_adicionais', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'hotel_configuracao',
            },
        ),
    ]
