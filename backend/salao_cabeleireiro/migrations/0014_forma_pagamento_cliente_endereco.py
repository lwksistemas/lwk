from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("salao_cabeleireiro", "0013_venda_comprovante"),
    ]

    operations = [
        migrations.AddField(
            model_name="cliente",
            name="cep",
            field=models.CharField(blank=True, default="", max_length=8),
        ),
        migrations.AddField(
            model_name="cliente",
            name="logradouro",
            field=models.CharField(blank=True, default="", max_length=160),
        ),
        migrations.AddField(
            model_name="cliente",
            name="numero",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
        migrations.AddField(
            model_name="cliente",
            name="complemento",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
        migrations.AddField(
            model_name="cliente",
            name="bairro",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
        migrations.AlterField(
            model_name="recebimento",
            name="forma",
            field=models.CharField(max_length=40),
        ),
        migrations.AlterField(
            model_name="venda",
            name="forma",
            field=models.CharField(default="dinheiro", max_length=40),
        ),
        migrations.CreateModel(
            name="FormaPagamento",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True)),
                ("codigo", models.CharField(max_length=40)),
                ("nome", models.CharField(max_length=40)),
                ("ativo", models.BooleanField(default=True)),
                ("ordem", models.PositiveSmallIntegerField(default=10)),
            ],
            options={
                "verbose_name": "Forma de pagamento",
                "ordering": ["ordem", "nome"],
            },
        ),
        migrations.AddConstraint(
            model_name="formapagamento",
            constraint=models.UniqueConstraint(fields=("loja_id", "codigo"), name="salao_forma_pagamento_loja"),
        ),
    ]
