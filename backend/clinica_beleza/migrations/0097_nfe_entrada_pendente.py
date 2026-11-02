from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0096_protocolo_personalizado_etapas"),
    ]

    operations = [
        migrations.CreateModel(
            name="NotaEntradaNfe",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("chave", models.CharField(max_length=44, verbose_name="Chave da NF-e")),
                ("numero", models.CharField(blank=True, default="", max_length=20)),
                ("fornecedor_nome", models.CharField(blank=True, default="", max_length=200)),
                ("fornecedor_documento", models.CharField(blank=True, default="", max_length=20)),
                ("destinatario_documento", models.CharField(blank=True, default="", max_length=20)),
                ("data_emissao", models.DateField(blank=True, null=True)),
                ("valor", models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
                ("xml", models.TextField(blank=True, default="")),
                ("status", models.CharField(
                    choices=[
                        ("resumo", "Aguardando XML"),
                        ("pendente", "Pendente"),
                        ("importada", "Importada"),
                        ("ignorada", "Ignorada"),
                    ],
                    default="pendente",
                    max_length=20,
                )),
                ("origem", models.CharField(default="arquivo", max_length=20)),
                ("nsu", models.CharField(blank=True, default="", max_length=20)),
                ("ultimo_erro", models.TextField(blank=True, default="")),
                ("importada_em", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "NF-e de entrada",
                "db_table": "clinica_beleza_notaentradanfe",
                "ordering": ["-data_emissao", "-id"],
            },
        ),
        migrations.AddConstraint(
            model_name="notaentradanfe",
            constraint=models.UniqueConstraint(fields=("loja_id", "chave"), name="cb_nfe_entrada_loja_chave"),
        ),
        migrations.CreateModel(
            name="NfeDistribuicaoEstado",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("ult_nsu", models.CharField(default="000000000000000", max_length=15)),
                ("max_nsu", models.CharField(default="000000000000000", max_length=15)),
                ("consultado_em", models.DateTimeField(blank=True, null=True)),
                ("ultimo_erro", models.TextField(blank=True, default="")),
            ],
            options={
                "db_table": "clinica_beleza_nfedistribuicaoestado",
            },
        ),
        migrations.AddConstraint(
            model_name="nfedistribuicaoestado",
            constraint=models.UniqueConstraint(fields=("loja_id",), name="cb_nfe_dist_loja"),
        ),
    ]
