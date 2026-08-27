from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0069_procedure_termo_template_unico"),
    ]

    operations = [
        migrations.AddField(
            model_name="appointment",
            name="confirmacao_generation",
            field=models.PositiveIntegerField(
                default=1,
                help_text="Incrementado ao alterar data, profissional ou procedimento. Invalida o link WhatsApp anterior.",
                verbose_name="Geração da confirmação",
            ),
        ),
    ]
