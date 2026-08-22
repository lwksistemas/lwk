from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Paciente",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("numero_prontuario", models.CharField(blank=True, default="", max_length=30)),
                ("medico_referencia", models.CharField(blank=True, default="", max_length=200)),
                ("nome", models.CharField(max_length=200)),
                ("nome_social", models.CharField(blank=True, default="", max_length=200)),
                ("data_nascimento", models.DateField(blank=True, null=True)),
                ("sexo", models.CharField(blank=True, choices=[("", "Não informado"), ("M", "Masculino"), ("F", "Feminino"), ("I", "Indefinido")], default="", max_length=1)),
                ("estado_civil", models.CharField(blank=True, default="", max_length=40)),
                ("cpf", models.CharField(blank=True, default="", max_length=14)),
                ("rg", models.CharField(blank=True, default="", max_length=20)),
                ("passaporte", models.CharField(blank=True, default="", max_length=30)),
                ("nome_mae", models.CharField(blank=True, default="", max_length=200)),
                ("tipo_sanguineo", models.CharField(blank=True, default="", max_length=8)),
                ("telefone", models.CharField(blank=True, default="", max_length=30)),
                ("email", models.EmailField(blank=True, default="", max_length=254)),
                ("cep", models.CharField(blank=True, default="", max_length=10)),
                ("logradouro", models.CharField(blank=True, default="", max_length=200)),
                ("numero", models.CharField(blank=True, default="", max_length=20)),
                ("complemento", models.CharField(blank=True, default="", max_length=80)),
                ("bairro", models.CharField(blank=True, default="", max_length=100)),
                ("cidade", models.CharField(blank=True, default="", max_length=100)),
                ("uf", models.CharField(blank=True, default="", max_length=2)),
                ("observacoes", models.TextField(blank=True, default="")),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "clinica_geral_paciente",
                "ordering": ["nome"],
            },
        ),
        migrations.CreateModel(
            name="Responsavel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("nome", models.CharField(max_length=200)),
                ("profissao", models.CharField(blank=True, default="", max_length=120)),
                ("parentesco", models.CharField(blank=True, default="", max_length=80)),
                ("telefone", models.CharField(blank=True, default="", max_length=30)),
                ("paciente", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="responsaveis", to="clinica_geral.paciente")),
            ],
            options={
                "db_table": "clinica_geral_responsavel",
            },
        ),
        migrations.CreateModel(
            name="ConvenioPaciente",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("convenio", models.CharField(max_length=120)),
                ("plano", models.CharField(blank=True, default="", max_length=120)),
                ("carteirinha", models.CharField(blank=True, default="", max_length=60)),
                ("validade", models.DateField(blank=True, null=True)),
                ("paciente", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="convenios", to="clinica_geral.paciente")),
            ],
            options={
                "db_table": "clinica_geral_convenio",
            },
        ),
        migrations.CreateModel(
            name="Consulta",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("data", models.DateField()),
                ("hora", models.TimeField()),
                ("tipo", models.CharField(choices=[("consulta", "Consulta"), ("primeira", "Primeira consulta"), ("retorno", "Retorno")], default="consulta", max_length=20)),
                ("modalidade", models.CharField(choices=[("presencial", "Consulta presencial"), ("tele", "Teleconsulta")], default="presencial", max_length=20)),
                ("convenio", models.CharField(blank=True, default="PARTICULAR", max_length=80)),
                ("status", models.CharField(choices=[("agendado", "Agendado"), ("confirmado", "Confirmado"), ("recepcionado", "Recepcionado"), ("desmarcado", "Desmarcado"), ("faltou", "Faltou")], default="agendado", max_length=20)),
                ("observacoes", models.TextField(blank=True, default="")),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("paciente", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="consultas", to="clinica_geral.paciente")),
            ],
            options={
                "db_table": "clinica_geral_consulta",
                "ordering": ["data", "hora"],
            },
        ),
        migrations.AddIndex(
            model_name="paciente",
            index=models.Index(fields=["loja_id", "is_active"], name="cg_pac_loja_act_idx"),
        ),
        migrations.AddIndex(
            model_name="paciente",
            index=models.Index(fields=["loja_id", "nome"], name="cg_pac_loja_nome_idx"),
        ),
        migrations.AddIndex(
            model_name="consulta",
            index=models.Index(fields=["loja_id", "data"], name="cg_cons_loja_data_idx"),
        ),
    ]
