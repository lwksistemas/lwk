from decimal import Decimal

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0097_nfe_entrada_pendente"),
    ]

    operations = [
        migrations.CreateModel(
            name="VinculoProdutoFornecedor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("documento", models.CharField(max_length=20, verbose_name="CPF/CNPJ do fornecedor")),
                ("codigo", models.CharField(max_length=60, verbose_name="Código na NF do fornecedor")),
                ("gtin", models.CharField(blank=True, default="", max_length=14, verbose_name="GTIN/EAN")),
                ("fator", models.DecimalField(
                    decimal_places=4,
                    default=Decimal("1"),
                    max_digits=10,
                    verbose_name="Unidades de estoque por unidade da nota",
                )),
                ("preco", models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name="Último custo unitário")),
                ("nome_no_fornecedor", models.CharField(blank=True, default="", max_length=200)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("produto", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="vinculos_fornecedor",
                    to="clinica_beleza.produtoestoque",
                )),
            ],
            options={
                "verbose_name": "Vínculo produto-fornecedor",
                "db_table": "clinica_beleza_vinculo_produto_fornecedor",
            },
        ),
        migrations.AddIndex(
            model_name="vinculoprodutofornecedor",
            index=models.Index(fields=["loja_id", "gtin"], name="cb_vinc_forn_gtin_idx"),
        ),
        migrations.AddConstraint(
            model_name="vinculoprodutofornecedor",
            constraint=models.UniqueConstraint(
                fields=("loja_id", "documento", "codigo"),
                name="cb_vinc_forn_codigo_uniq",
            ),
        ),
    ]
