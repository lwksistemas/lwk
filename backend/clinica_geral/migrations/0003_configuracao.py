from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_geral", "0002_agenda_fluxo"),
    ]

    operations = [
        migrations.CreateModel(
            name="ConfiguracaoConsultorio",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("hora_inicio", models.TimeField(default="08:00")),
                ("hora_fim", models.TimeField(default="18:00")),
                ("duracao_minutos", models.PositiveSmallIntegerField(default=15)),
                ("endereco", models.CharField(blank=True, default="", max_length=240)),
                ("telefone", models.CharField(blank=True, default="", max_length=30)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "clinica_geral_config",
            },
        ),
    ]
