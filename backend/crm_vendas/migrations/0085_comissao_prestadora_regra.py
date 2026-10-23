from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm_vendas", "0084_categoria_subpasta"),
    ]

    operations = [
        migrations.AddField(
            model_name="conta",
            name="comissao_escopo",
            field=models.CharField(
                choices=[
                    ("todos", "Todos os produtos e serviços"),
                    ("especificos", "Produtos e serviços escolhidos"),
                ],
                default="especificos",
                help_text="Se a prestadora paga em todos os serviços ou só nos escolhidos",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="conta",
            name="comissao_tipo",
            field=models.CharField(
                choices=[("percentual", "Porcentagem"), ("fixo", "Valor fixo")],
                default="percentual",
                help_text="Porcentagem do preço ou valor fixo, quando vale para todos",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="conta",
            name="comissao_valor",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Porcentagem ou valor fixo que a prestadora paga em todos os serviços",
                max_digits=12,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="contaprodutocomissao",
            name="tipo",
            field=models.CharField(
                choices=[("fixo", "Valor fixo"), ("percentual", "Porcentagem")],
                default="fixo",
                help_text="Porcentagem do preço ou valor fixo em reais",
                max_length=20,
            ),
        ),
    ]
