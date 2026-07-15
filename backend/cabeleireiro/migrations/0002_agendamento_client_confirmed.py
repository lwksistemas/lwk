from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cabeleireiro", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="agendamento",
            name="status",
            field=models.CharField(
                choices=[
                    ("SCHEDULED", "Agendado"),
                    ("CLIENT_CONFIRMED", "Confirmado pelo cliente"),
                    ("ARRIVED", "Chegou"),
                    ("IN_PROGRESS", "Em atendimento"),
                    ("DONE", "Concluído"),
                    ("NO_SHOW", "Não compareceu"),
                    ("CANCELLED", "Cancelado"),
                ],
                default="SCHEDULED",
                max_length=20,
            ),
        ),
    ]
