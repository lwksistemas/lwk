from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0104_intervalo_agenda_profissional"),
    ]

    operations = [
        migrations.CreateModel(
            name="SimulacaoEsteticaConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("provedor", models.CharField(choices=[("youcam", "YouCam API")], default="youcam", max_length=20)),
                ("api_key", models.TextField(blank=True, default="")),
                ("ativa", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Simulação estética",
                "db_table": "clinica_beleza_simulacao_estetica_config",
                "constraints": [
                    models.UniqueConstraint(fields=("loja_id",), name="uniq_simulacao_estetica_loja"),
                ],
            },
        ),
    ]
