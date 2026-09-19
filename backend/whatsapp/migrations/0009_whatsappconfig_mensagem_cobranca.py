# Mensagem padrão de cobrança por loja (inadimplência).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("whatsapp", "0008_confirmacao_antecedencias"),
    ]

    operations = [
        migrations.AddField(
            model_name="whatsappconfig",
            name="mensagem_cobranca",
            field=models.TextField(
                blank=True,
                default="",
                help_text=(
                    "Placeholders: {nome}, {valor}, {vencimento}, {dias_atraso}, {clinica}. "
                    "Deixe em branco para usar a mensagem padrão."
                ),
                verbose_name="Mensagem personalizada de cobrança",
            ),
        ),
    ]
