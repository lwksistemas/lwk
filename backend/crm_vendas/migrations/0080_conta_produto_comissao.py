from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("crm_vendas", "0079_crmconfig_colunas_propostas_contratos"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContaProdutoComissao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                (
                    "valor",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        help_text="Valor em reais que a prestadora paga à loja por este item",
                        max_digits=12,
                    ),
                ),
                (
                    "conta",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="comissoes_produtos",
                        to="crm_vendas.conta",
                    ),
                ),
                (
                    "produto_servico",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="comissoes_prestadoras",
                        to="crm_vendas.produtoservico",
                    ),
                ),
            ],
            options={
                "verbose_name": "Comissão da prestadora",
                "verbose_name_plural": "Comissões da prestadora",
                "db_table": "crm_vendas_conta_produto_comissao",
                "indexes": [
                    models.Index(fields=["loja_id", "conta"], name="crm_cpc_loja_conta_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("conta", "produto_servico"),
                        name="crm_conta_prod_comissao_uniq",
                    ),
                ],
            },
        ),
    ]
