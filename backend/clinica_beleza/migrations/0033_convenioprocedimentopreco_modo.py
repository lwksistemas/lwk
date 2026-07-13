# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0032_convenio"),
    ]

    operations = [
        migrations.AddField(
            model_name="convenioprocedimentopreco",
            name="modo",
            field=models.CharField(
                choices=[("fixo", "Valor fixo (R$)"), ("percentual", "Percentual (%)")],
                default="fixo",
                max_length=15,
                verbose_name="Modo",
            ),
        ),
        migrations.AlterField(
            model_name="convenioprocedimentopreco",
            name="preco",
            field=models.DecimalField(
                decimal_places=2,
                help_text="Valor fixo em R$ ou percentual sobre o preço particular (ex: 70 = 70%).",
                max_digits=10,
                verbose_name="Valor",
            ),
        ),
    ]
