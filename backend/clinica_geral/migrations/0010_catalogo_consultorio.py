from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("clinica_geral", "0009_equipe_especialidade"),
    ]

    operations = [
        migrations.AddField(
            model_name="configuracaoconsultorio",
            name="cep",
            field=models.CharField(blank=True, default="", max_length=10),
        ),
        migrations.AddField(
            model_name="configuracaoconsultorio",
            name="logradouro",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="configuracaoconsultorio",
            name="numero",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
        migrations.AddField(
            model_name="configuracaoconsultorio",
            name="complemento",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
        migrations.AddField(
            model_name="configuracaoconsultorio",
            name="bairro",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="configuracaoconsultorio",
            name="cidade",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="configuracaoconsultorio",
            name="uf",
            field=models.CharField(blank=True, default="", max_length=2),
        ),
        migrations.AddField(
            model_name="configuracaoconsultorio",
            name="prontuario_prefixo",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
        migrations.AddField(
            model_name="configuracaoconsultorio",
            name="prontuario_abas_ocultas",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AlterField(
            model_name="consulta",
            name="tipo",
            field=models.CharField(default="consulta", max_length=40),
        ),
        migrations.CreateModel(
            name="TipoConsulta",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("codigo", models.CharField(max_length=40)),
                ("nome", models.CharField(max_length=80)),
                ("duracao_minutos", models.PositiveSmallIntegerField(default=0)),
                ("valor", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("ordem", models.PositiveSmallIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "clinica_geral_tipo_consulta",
                "ordering": ["ordem", "nome"],
                "unique_together": {("loja_id", "codigo")},
                "indexes": [models.Index(fields=["loja_id", "is_active"], name="cg_tipo_loja_act_idx")],
            },
        ),
        migrations.CreateModel(
            name="ConvenioConsultorio",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("nome", models.CharField(max_length=120)),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("particular", "Particular"),
                            ("convenio", "Convênio"),
                            ("empresa", "Empresa"),
                            ("adm", "Adm. de benefícios"),
                        ],
                        default="convenio",
                        max_length=20,
                    ),
                ),
                ("registro_ans", models.CharField(blank=True, default="", max_length=20)),
                ("telefone", models.CharField(blank=True, default="", max_length=30)),
                ("observacoes", models.CharField(blank=True, default="", max_length=200)),
                ("ordem", models.PositiveSmallIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "clinica_geral_convenio_cat",
                "ordering": ["ordem", "nome"],
                "unique_together": {("loja_id", "nome")},
                "indexes": [models.Index(fields=["loja_id", "is_active"], name="cg_convcat_loja_act_idx")],
            },
        ),
    ]
