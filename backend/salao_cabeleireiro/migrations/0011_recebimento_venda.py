import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("salao_cabeleireiro", "0010_comissao_procedimento"),
    ]

    operations = [
        migrations.AddField(
            model_name="recebimento",
            name="venda",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="recebimentos_da_venda",
                to="salao_cabeleireiro.venda",
            ),
        ),
    ]
