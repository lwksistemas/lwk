from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("superadmin", "0079_loja_recibo_endereco_documento"),
    ]

    operations = [
        migrations.AddField(
            model_name="planoassinatura",
            name="tem_agendamento_online",
            field=models.BooleanField(
                default=False,
                help_text="Permite a clínica oferecer agendamento pela internet.",
            ),
        ),
    ]
