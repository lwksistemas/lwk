import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("salao_cabeleireiro", "0015_caixa_fechamento_cancelamento"),
    ]

    operations = [
        migrations.CreateModel(
            name="Categoria",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True)),
                ("nome", models.CharField(max_length=100)),
                ("ordem", models.PositiveSmallIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"verbose_name": "Categoria de procedimento", "ordering": ["ordem", "nome"]},
        ),
        migrations.AddConstraint(
            model_name="categoria",
            constraint=models.UniqueConstraint(
                condition=models.Q(is_active=True),
                fields=("loja_id", "nome"),
                name="salao_categoria_ativa",
            ),
        ),
        migrations.CreateModel(
            name="AgendamentoProcedimento",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True)),
                ("ordem", models.PositiveSmallIntegerField(default=0)),
                (
                    "agendamento",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="procedimentos",
                        to="salao_cabeleireiro.agendamento",
                    ),
                ),
                (
                    "servico",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="usos",
                        to="salao_cabeleireiro.servico",
                    ),
                ),
            ],
            options={"verbose_name": "Procedimento do horário", "ordering": ["ordem", "id"]},
        ),
        migrations.AddConstraint(
            model_name="agendamentoprocedimento",
            constraint=models.UniqueConstraint(fields=("agendamento", "servico"), name="salao_horario_procedimento"),
        ),
    ]
