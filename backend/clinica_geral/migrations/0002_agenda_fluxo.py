from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_geral", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="paciente",
            name="rne",
            field=models.CharField(blank=True, default="", max_length=30),
        ),
        migrations.AddField(
            model_name="paciente",
            name="pais_emissor",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
        migrations.AddField(
            model_name="paciente",
            name="telefone_fixo",
            field=models.CharField(blank=True, default="", max_length=30),
        ),
        migrations.AddField(
            model_name="paciente",
            name="quem_indicou",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="consulta",
            name="duracao_minutos",
            field=models.PositiveSmallIntegerField(default=15),
        ),
        migrations.AddField(
            model_name="consulta",
            name="agendado_por",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AlterField(
            model_name="consulta",
            name="status",
            field=models.CharField(
                choices=[
                    ("agendado", "Agendado"),
                    ("confirmado", "Confirmado"),
                    ("recepcionado", "Recepcionado"),
                    ("atendido", "Atendido"),
                    ("desmarcado", "Desmarcado"),
                    ("faltou", "Faltou"),
                ],
                default="agendado",
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name="Tarefa",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("data", models.DateField()),
                ("texto", models.CharField(max_length=240)),
                ("concluida", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "clinica_geral_tarefa",
                "ordering": ["-id"],
            },
        ),
    ]
