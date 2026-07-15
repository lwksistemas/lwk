import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cabeleireiro", "0002_agendamento_client_confirmed"),
    ]

    operations = [
        migrations.CreateModel(
            name="BloqueioHorario",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("titulo", models.CharField(max_length=200, verbose_name="Título")),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("feriado", "Feriado"),
                            ("ferias", "Férias"),
                            ("folga", "Folga"),
                            ("manutencao", "Manutenção"),
                            ("evento", "Evento"),
                            ("outros", "Outros"),
                        ],
                        max_length=20,
                        verbose_name="Tipo",
                    ),
                ),
                ("data_inicio", models.DateField(verbose_name="Data Início")),
                ("data_fim", models.DateField(verbose_name="Data Fim")),
                (
                    "horario_inicio",
                    models.TimeField(
                        blank=True,
                        help_text="Deixe vazio para bloquear o dia todo",
                        null=True,
                        verbose_name="Horário Início",
                    ),
                ),
                ("horario_fim", models.TimeField(blank=True, null=True, verbose_name="Horário Fim")),
                ("observacoes", models.TextField(blank=True, null=True, verbose_name="Observações")),
                ("is_active", models.BooleanField(default=True, verbose_name="Ativo")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("motivo", models.CharField(max_length=100, verbose_name="Motivo")),
                ("criado_em", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                (
                    "profissional",
                    models.ForeignKey(
                        blank=True,
                        help_text="Vazio = bloqueio geral (todos)",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="bloqueios",
                        to="cabeleireiro.profissional",
                        verbose_name="Profissional",
                    ),
                ),
            ],
            options={
                "verbose_name": "Bloqueio de Horário",
                "verbose_name_plural": "Bloqueios de Horário",
                "db_table": "cabeleireiro_bloqueiohorario",
                "ordering": ["-data_inicio"],
                "indexes": [
# Index names must stay <= 30 chars for PostgreSQL
                    models.Index(fields=["data_inicio", "data_fim"], name="cab_bloq_data_idx"),
                    models.Index(fields=["profissional", "data_inicio"], name="cab_bloq_prof_idx"),
                    models.Index(fields=["loja_id", "data_inicio"], name="cab_bloq_loja_idx"),
                ],
            },
        ),
    ]
