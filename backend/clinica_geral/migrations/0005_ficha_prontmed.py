from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("clinica_geral", "0004_consultorio_modulos"),
    ]

    operations = [
        migrations.AddField(
            model_name="paciente",
            name="nacionalidade",
            field=models.CharField(blank=True, default="Brasileira", max_length=80),
        ),
        migrations.AddField(
            model_name="paciente",
            name="profissao",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddField(
            model_name="paciente",
            name="foto_url",
            field=models.CharField(blank=True, default="", max_length=500),
        ),
        migrations.CreateModel(
            name="PacienteAnexo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True)),
                ("nome", models.CharField(max_length=200)),
                ("url", models.CharField(max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "paciente",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="anexos",
                        to="clinica_geral.paciente",
                    ),
                ),
            ],
            options={
                "db_table": "clinica_geral_anexo",
                "ordering": ["-id"],
            },
        ),
    ]
