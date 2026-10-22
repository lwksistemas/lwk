from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm_vendas", "0081_vendedor_categoria_comissao"),
    ]

    operations = [
        migrations.AddField(
            model_name="conta",
            name="logo",
            field=models.URLField(
                blank=True,
                default="",
                help_text="Logomarca da prestadora, usada na proposta e no contrato",
                max_length=500,
            ),
        ),
    ]
