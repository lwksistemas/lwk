from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("clinica_geral", "0008_perfil_profissional"),
    ]

    operations = [
        migrations.CreateModel(
            name="Especialidade",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("nome", models.CharField(max_length=120)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "clinica_geral_especialidade",
                "ordering": ["nome"],
                "unique_together": {("loja_id", "nome")},
                "indexes": [models.Index(fields=["loja_id", "is_active"], name="cg_esp_loja_act_idx")],
            },
        ),
        migrations.CreateModel(
            name="Profissional",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("nome", models.CharField(max_length=200)),
                ("conselho", models.CharField(blank=True, default="", max_length=20)),
                ("registro", models.CharField(blank=True, default="", max_length=30)),
                ("uf", models.CharField(blank=True, default="", max_length=2)),
                ("email", models.EmailField(blank=True, default="", max_length=254)),
                ("telefone", models.CharField(blank=True, default="", max_length=30)),
                ("cbo", models.CharField(blank=True, default="", max_length=20)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "especialidade",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profissionais",
                        to="clinica_geral.especialidade",
                    ),
                ),
            ],
            options={
                "db_table": "clinica_geral_profissional",
                "ordering": ["nome"],
                "indexes": [models.Index(fields=["loja_id", "especialidade"], name="cg_prof_loja_esp_idx")],
            },
        ),
        migrations.CreateModel(
            name="Funcionario",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("nome", models.CharField(max_length=200)),
                (
                    "cargo",
                    models.CharField(
                        choices=[
                            ("recepcao", "Recepção"),
                            ("administracao", "Administração"),
                            ("financeiro", "Financeiro"),
                            ("outros", "Outros"),
                        ],
                        default="recepcao",
                        max_length=20,
                    ),
                ),
                ("email", models.EmailField(blank=True, default="", max_length=254)),
                ("telefone", models.CharField(blank=True, default="", max_length=30)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "clinica_geral_funcionario",
                "ordering": ["nome"],
                "indexes": [models.Index(fields=["loja_id", "is_active"], name="cg_func_loja_act_idx")],
            },
        ),
    ]
