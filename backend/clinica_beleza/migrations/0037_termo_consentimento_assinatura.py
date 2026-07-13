# Generated manually — termo de consentimento e assinatura digital em consultas
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0036_professional_commission_convenio"),
    ]

    operations = [
        migrations.AddField(
            model_name="procedure",
            name="termo_consentimento",
            field=models.TextField(blank=True, default="", verbose_name="Termo de consentimento"),
        ),
        migrations.AddField(
            model_name="procedure",
            name="termo_consentimento_ativo",
            field=models.BooleanField(default=False, verbose_name="Termo de consentimento ativo"),
        ),
        migrations.AddField(
            model_name="produtoestoque",
            name="procedure",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="produtos_estoque",
                to="clinica_beleza.procedure",
                verbose_name="Procedimento vinculado",
            ),
        ),
        migrations.AddField(
            model_name="consulta",
            name="status_assinatura_termo",
            field=models.CharField(
                choices=[
                    ("rascunho", "Rascunho"),
                    ("aguardando_paciente", "Aguardando Paciente"),
                    ("aguardando_profissional", "Aguardando Profissional"),
                    ("concluido", "Concluído"),
                ],
                default="rascunho",
                max_length=30,
                verbose_name="Status assinatura termo",
            ),
        ),
        migrations.AddField(
            model_name="consulta",
            name="conteudo_termo_consentimento",
            field=models.TextField(blank=True, default="", verbose_name="Conteúdo do termo"),
        ),
        migrations.CreateModel(
            name="ConsultaAssinaturaTermo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True)),
                ("tipo", models.CharField(choices=[("paciente", "Paciente"), ("profissional", "Profissional")], max_length=15)),
                ("nome_assinante", models.CharField(max_length=200)),
                ("email_assinante", models.EmailField(max_length=254)),
                ("ip_address", models.GenericIPAddressField(default="0.0.0.0")),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                ("user_agent", models.TextField(blank=True, default="")),
                ("token", models.CharField(db_index=True, max_length=255, unique=True)),
                ("token_expira_em", models.DateTimeField()),
                ("assinado", models.BooleanField(default=False)),
                ("assinado_em", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("consulta", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assinaturas_termo", to="clinica_beleza.consulta")),
            ],
            options={
                "verbose_name": "Assinatura de termo de consentimento",
                "verbose_name_plural": "Assinaturas de termo de consentimento",
                "db_table": "clinica_beleza_consulta_assinaturas_termo",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="consultaassinaturatermo",
            index=models.Index(fields=["loja_id", "token"], name="clin_cb_assin_loja_tok_idx"),
        ),
        migrations.AddIndex(
            model_name="consultaassinaturatermo",
            index=models.Index(fields=["consulta", "tipo"], name="clin_cb_assin_cons_tipo_idx"),
        ),
    ]
