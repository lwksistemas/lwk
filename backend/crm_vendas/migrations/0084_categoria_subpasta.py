from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm_vendas", "0083_produto_prestadora"),
    ]

    operations = [
        migrations.AddField(
            model_name="categoriaprodutoservico",
            name="pai",
            field=models.ForeignKey(
                blank=True,
                help_text="Categoria acima desta subpasta. A oportunidade abre uma pasta de cada vez.",
                null=True,
                on_delete=models.CASCADE,
                related_name="subpastas",
                to="crm_vendas.categoriaprodutoservico",
            ),
        ),
        migrations.AddIndex(
            model_name="categoriaprodutoservico",
            index=models.Index(fields=["loja_id", "pai"], name="crm_cat_ps_loja_pai_idx"),
        ),
    ]
