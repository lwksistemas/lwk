# Generated manually for Google Calendar OAuth (CRM Vendas)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0032_alter_planoassinatura_tipos_loja_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='GoogleCalendarConnection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.IntegerField(db_index=True, unique=True)),
                ('access_token', models.TextField(blank=True)),
                ('refresh_token', models.TextField(blank=True)),
                ('token_expiry', models.DateTimeField(blank=True, null=True)),
                ('calendar_id', models.CharField(default='primary', max_length=255)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Conexão Google Calendar (CRM)',
                'verbose_name_plural': 'Conexões Google Calendar (CRM)',
                'db_table': 'superadmin_google_calendar_connection',
            },
        ),
    ]
