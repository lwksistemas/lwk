from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("crm_vendas", "0080_conta_produto_comissao"),
    ]

    operations = [
        migrations.CreateModel(
            name="VendedorCategoriaComissao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                (
                    "tipo",
                    models.CharField(
                        choices=[("fixo", "Valor fixo"), ("percentual", "Porcentagem")],
                        default="percentual",
                        max_length=20,
                    ),
                ),
                (
                    "valor",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        help_text="Reais por unidade, quando o tipo é valor fixo. Percentual, quando o tipo é porcentagem.",
                        max_digits=12,
                    ),
                ),
                (
                    "categoria",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="comissoes_vendedores",
                        to="crm_vendas.categoriaprodutoservico",
                    ),
                ),
                (
                    "vendedor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="comissoes_categoria",
                        to="crm_vendas.vendedor",
                    ),
                ),
            ],
            options={
                "verbose_name": "Comissão do vendedor por categoria",
                "verbose_name_plural": "Comissões do vendedor por categoria",
                "db_table": "crm_vendas_vendedor_categoria_comissao",
                "indexes": [
                    models.Index(fields=["loja_id", "vendedor"], name="crm_vcc_loja_vend_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("vendedor", "categoria"),
                        name="crm_vend_cat_comissao_uniq",
                    ),
                ],
            },
        ),
    ]
