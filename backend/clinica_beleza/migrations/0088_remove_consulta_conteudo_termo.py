from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0087_appointment_created_by"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="consulta",
            name="conteudo_termo_consentimento",
        ),
    ]
