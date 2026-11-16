from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("salao_cabeleireiro", "0007_produto_venda"),
    ]

    operations = [
        migrations.CreateModel(
            name="NotaEntradaSalao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True)),
                ("chave", models.CharField(max_length=44)),
                ("numero", models.CharField(blank=True, default="", max_length=20)),
                ("fornecedor_nome", models.CharField(blank=True, default="", max_length=200)),
                ("fornecedor_documento", models.CharField(blank=True, default="", max_length=20)),
                ("destinatario_documento", models.CharField(blank=True, default="", max_length=20)),
                ("data_emissao", models.DateField(blank=True, null=True)),
                ("valor", models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
                ("xml", models.TextField(blank=True, default="")),
                ("status", models.CharField(default="pendente", max_length=20)),
                ("origem", models.CharField(default="arquivo", max_length=20)),
                ("nsu", models.CharField(blank=True, default="", max_length=20)),
                ("ultimo_erro", models.TextField(blank=True, default="")),
                ("importada_em", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "NF-e de entrada", "ordering": ["-data_emissao", "-id"]},
        ),
        migrations.CreateModel(
            name="NfeDistribuicaoSalao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True)),
                ("ult_nsu", models.CharField(default="000000000000000", max_length=15)),
                ("max_nsu", models.CharField(default="000000000000000", max_length=15)),
                ("consultado_em", models.DateTimeField(blank=True, null=True)),
                ("ultimo_erro", models.TextField(blank=True, default="")),
            ],
            options={"verbose_name": "Consulta de NF-e"},
        ),
        migrations.AddConstraint(
            model_name="notaentradasalao",
            constraint=models.UniqueConstraint(fields=("loja_id", "chave"), name="salao_nfe_entrada_loja_chave"),
        ),
        migrations.AddConstraint(
            model_name="nfedistribuicaosalao",
            constraint=models.UniqueConstraint(fields=("loja_id",), name="salao_nfe_dist_loja"),
        ),
    ]
