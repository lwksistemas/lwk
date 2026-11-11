import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0108_despesa_nota_fiscal"),
    ]

    operations = [
        migrations.AddField(
            model_name="vinculoprodutofornecedor",
            name="uso_consumo",
            field=models.BooleanField(default=False, verbose_name="Uso e consumo"),
        ),
        migrations.AlterField(
            model_name="vinculoprodutofornecedor",
            name="produto",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="vinculos_fornecedor",
                to="clinica_beleza.produtoestoque",
            ),
        ),
    ]
