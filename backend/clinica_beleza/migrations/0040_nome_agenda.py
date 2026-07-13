import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0039_paciente_foto_acompanhamento"),
    ]

    operations = [
        migrations.CreateModel(
            name="NomeAgenda",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True)),
                ("nome", models.CharField(max_length=200, verbose_name="Nome da agenda")),
                ("is_active", models.BooleanField(default=True, verbose_name="Ativo")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Nome da agenda",
                "verbose_name_plural": "Nomes de agenda",
                "db_table": "clinica_beleza_nomes_agenda",
                "ordering": ["nome"],
            },
        ),
        migrations.AddField(
            model_name="appointment",
            name="nome_agenda",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="agendamentos",
                to="clinica_beleza.nomeagenda",
                verbose_name="Nome da agenda",
            ),
        ),
    ]
