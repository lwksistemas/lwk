from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0067_nfse_config_padrao_nacional_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="TermoConsentimentoTemplate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True)),
                ("nome", models.CharField(max_length=200, verbose_name="Nome")),
                ("tipo", models.CharField(
                    choices=[("simples", "Termo simples"), ("interativo", "TCLE Interativo")],
                    default="simples",
                    max_length=20,
                    verbose_name="Tipo",
                )),
                ("introducao", models.TextField(blank=True, default="", verbose_name="Introdução")),
                ("conteudo", models.TextField(blank=True, default="", verbose_name="Texto do termo simples")),
                ("secoes", models.JSONField(blank=True, default=list, verbose_name="Seções do TCLE Interativo")),
                ("is_active", models.BooleanField(default=True, verbose_name="Ativo")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Template de termo de consentimento",
                "verbose_name_plural": "Templates de termo de consentimento",
                "db_table": "clinica_beleza_termo_template",
                "ordering": ["nome"],
            },
        ),
        migrations.CreateModel(
            name="TermoConsentimentoConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True)),
                ("pdf_cabecalho", models.CharField(
                    choices=[("logo", "Logomarca da clínica"), ("timbrado", "Papel timbrado")],
                    default="logo",
                    max_length=20,
                    verbose_name="Cabeçalho do PDF",
                )),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Configuração de termo de consentimento",
                "verbose_name_plural": "Configurações de termo de consentimento",
                "db_table": "clinica_beleza_termo_config",
            },
        ),
        migrations.AddField(
            model_name="procedure",
            name="termo_template",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="procedimentos",
                to="clinica_beleza.termoconsentimentotemplate",
                verbose_name="Template de termo",
            ),
        ),
        migrations.AddField(
            model_name="consultatermoprocedimento",
            name="respostas_interativo",
            field=models.JSONField(blank=True, default=dict, verbose_name="Respostas do TCLE Interativo"),
        ),
    ]
