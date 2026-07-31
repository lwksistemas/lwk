from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm_vendas", "0071_produtoservico_recorrencia_semestral"),
    ]

    operations = [
        migrations.AddField(
            model_name="crmconfig",
            name="nacional_codigo_municipio",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Código IBGE de 7 dígitos do município de prestação (ex.: 3543402 Ribeirão Preto).",
                max_length=7,
                verbose_name="Código IBGE do município (API Nacional)",
            ),
        ),
    ]
