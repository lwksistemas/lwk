import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cabeleireiro", "0003_bloqueio_horario"),
    ]

    operations = [
        migrations.CreateModel(
            name="CategoriaServico",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("nome", models.CharField(max_length=100, verbose_name="Nome")),
                ("ordem", models.PositiveIntegerField(default=0, verbose_name="Ordem")),
                ("is_active", models.BooleanField(default=True, verbose_name="Ativo")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Categoria de serviço",
                "verbose_name_plural": "Categorias de serviço",
                "db_table": "cabeleireiro_categoriaservico",
                "ordering": ["ordem", "nome"],
                "indexes": [
                    models.Index(fields=["loja_id", "is_active"], name="cab_cat_loja_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="HorarioTrabalhoProfissional",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                (
                    "dia_semana",
                    models.IntegerField(
                        choices=[
                            (0, "Segunda-feira"),
                            (1, "Terça-feira"),
                            (2, "Quarta-feira"),
                            (3, "Quinta-feira"),
                            (4, "Sexta-feira"),
                            (5, "Sábado"),
                            (6, "Domingo"),
                        ],
                        verbose_name="Dia da semana",
                    ),
                ),
                ("hora_entrada", models.TimeField(verbose_name="Entrada")),
                ("hora_saida", models.TimeField(verbose_name="Saída")),
                (
                    "intervalo_inicio",
                    models.TimeField(
                        blank=True,
                        help_text="Opcional (ex: almoço)",
                        null=True,
                        verbose_name="Início intervalo",
                    ),
                ),
                ("intervalo_fim", models.TimeField(blank=True, null=True, verbose_name="Fim intervalo")),
                ("ativo", models.BooleanField(default=True, verbose_name="Ativo")),
                (
                    "profissional",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="horarios_trabalho",
                        to="cabeleireiro.profissional",
                        verbose_name="Profissional",
                    ),
                ),
            ],
            options={
                "verbose_name": "Horário de trabalho",
                "verbose_name_plural": "Horários de trabalho",
                "db_table": "cabeleireiro_horariotrabalhoprofissional",
                "ordering": ["profissional", "dia_semana"],
                "unique_together": {("profissional", "dia_semana")},
                "indexes": [
                    models.Index(fields=["profissional", "dia_semana"], name="cab_ht_prof_dia_idx"),
                    models.Index(fields=["loja_id", "profissional"], name="cab_ht_loja_prof_idx"),
                ],
            },
        ),
    ]
