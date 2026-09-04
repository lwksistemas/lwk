from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_geral", "0003_configuracao"),
    ]

    operations = [
        migrations.AddField(
            model_name="paciente",
            name="alergias",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="consulta",
            name="valor",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name="consulta",
            name="tele_sala_url",
            field=models.CharField(blank=True, default="", max_length=400),
        ),
        migrations.AddField(
            model_name="consulta",
            name="tele_minutos",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="consulta",
            name="status",
            field=models.CharField(
                choices=[
                    ("agendado", "Agendado"),
                    ("confirmado", "Confirmado"),
                    ("checkin", "Check-in"),
                    ("recepcionado", "Recepcionado"),
                    ("atendido", "Atendido"),
                    ("desmarcado", "Desmarcado"),
                    ("faltou", "Faltou"),
                ],
                default="agendado",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="configuracaoconsultorio",
            name="especialidade",
            field=models.CharField(blank=True, default="Clínica médica", max_length=80),
        ),
        migrations.AddField(
            model_name="configuracaoconsultorio",
            name="crm",
            field=models.CharField(blank=True, default="", max_length=30),
        ),
        migrations.AddField(
            model_name="configuracaoconsultorio",
            name="medico_nome",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="configuracaoconsultorio",
            name="teto_tele_minutos",
            field=models.PositiveIntegerField(default=600),
        ),
        migrations.CreateModel(
            name="Evolucao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("especialidade", models.CharField(blank=True, default="", max_length=80)),
                ("subjetivo", models.TextField(blank=True, default="")),
                ("objetivo", models.TextField(blank=True, default="")),
                ("avaliacao", models.TextField(blank=True, default="")),
                ("plano", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "consulta",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="evolucao",
                        to="clinica_geral.consulta",
                    ),
                ),
                (
                    "paciente",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="evolucoes",
                        to="clinica_geral.paciente",
                    ),
                ),
            ],
            options={"db_table": "clinica_geral_evolucao", "ordering": ["-id"]},
        ),
        migrations.CreateModel(
            name="Prescricao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "consulta",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="prescricoes",
                        to="clinica_geral.consulta",
                    ),
                ),
                (
                    "paciente",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="prescricoes",
                        to="clinica_geral.paciente",
                    ),
                ),
            ],
            options={"db_table": "clinica_geral_prescricao", "ordering": ["-id"]},
        ),
        migrations.CreateModel(
            name="PrescricaoItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("medicamento", models.CharField(max_length=200)),
                ("dosagem", models.CharField(blank=True, default="", max_length=80)),
                ("posologia", models.CharField(blank=True, default="", max_length=240)),
                ("quantidade", models.CharField(blank=True, default="", max_length=40)),
                ("alerta_alergia", models.BooleanField(default=False)),
                (
                    "prescricao",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="itens",
                        to="clinica_geral.prescricao",
                    ),
                ),
            ],
            options={"db_table": "clinica_geral_prescricao_item"},
        ),
        migrations.CreateModel(
            name="LoteTiss",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("numero", models.CharField(blank=True, default="", max_length=30)),
                ("competencia", models.CharField(blank=True, default="", max_length=7)),
                ("status", models.CharField(choices=[("aberto", "Aberto"), ("fechado", "Fechado")], default="aberto", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "clinica_geral_lote_tiss", "ordering": ["-id"]},
        ),
        migrations.CreateModel(
            name="GuiaTiss",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("numero_guia", models.CharField(blank=True, default="", max_length=30)),
                ("codigo_procedimento", models.CharField(blank=True, default="10101012", max_length=20)),
                ("valor", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "consulta",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="guia_tiss",
                        to="clinica_geral.consulta",
                    ),
                ),
                (
                    "lote",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="guias",
                        to="clinica_geral.lotetiss",
                    ),
                ),
            ],
            options={"db_table": "clinica_geral_guia_tiss", "ordering": ["-id"]},
        ),
        migrations.CreateModel(
            name="FechamentoCaixa",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("data", models.DateField()),
                ("total_particular", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("total_convenio", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("observacoes", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "clinica_geral_caixa", "ordering": ["-data"], "unique_together": {("loja_id", "data")}},
        ),
    ]
