from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0086_asaas_api_key_text"),
    ]

    operations = [
        migrations.AddField(
            model_name="appointment",
            name="created_by_id",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Usuário autenticado que criou o agendamento. Não muda nas edições seguintes.",
                null=True,
                verbose_name="Criado por (user id)",
            ),
        ),
    ]
