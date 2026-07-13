from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("whatsapp", "0006_whatsapp_proposta_contrato_termo"),
    ]

    operations = [
        migrations.AddField(
            model_name="whatsappconfig",
            name="mensagem_confirmacao_agenda",
            field=models.TextField(
                blank=True,
                default="",
                help_text=(
                    "Placeholders: {nome}, {data}, {hora}, {procedimento}, {profissional}, {link}. "
                    "Deixe em branco para usar a mensagem padrão."
                ),
                verbose_name="Mensagem personalizada de confirmação de agendamento",
            ),
        ),
    ]
