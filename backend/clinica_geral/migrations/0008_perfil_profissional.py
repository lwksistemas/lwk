from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("clinica_geral", "0007_tele_token"),
    ]

    operations = [
        migrations.CreateModel(
            name="PerfilProfissional",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("username", models.CharField(max_length=150)),
                ("tratamento", models.CharField(blank=True, default="", max_length=20)),
                ("celular", models.CharField(blank=True, default="", max_length=30)),
                ("telefone", models.CharField(blank=True, default="", max_length=30)),
                ("conselho", models.CharField(blank=True, default="", max_length=20)),
                ("uf", models.CharField(blank=True, default="", max_length=2)),
                ("rg", models.CharField(blank=True, default="", max_length=20)),
                ("cpf", models.CharField(blank=True, default="", max_length=14)),
                ("data_nascimento", models.DateField(blank=True, null=True)),
                ("nacionalidade", models.CharField(blank=True, default="", max_length=80)),
                (
                    "sexo",
                    models.CharField(
                        blank=True,
                        choices=[("", "Não informado"), ("M", "Masculino"), ("F", "Feminino"), ("I", "Indefinido")],
                        default="",
                        max_length=1,
                    ),
                ),
                ("cbo", models.CharField(blank=True, default="", max_length=20)),
                (
                    "estado_civil",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("", "Não informado"),
                            ("solteiro", "Solteiro(a)"),
                            ("casado", "Casado(a)"),
                            ("divorciado", "Divorciado(a)"),
                            ("viuvo", "Viúvo(a)"),
                            ("uniao", "União estável"),
                        ],
                        default="",
                        max_length=20,
                    ),
                ),
                ("foto_url", models.CharField(blank=True, default="", max_length=500)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "clinica_geral_perfil",
                "unique_together": {("loja_id", "username")},
            },
        ),
    ]
