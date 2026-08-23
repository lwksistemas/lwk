from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("clinica_geral", "0006_ficha_atendimento"),
    ]

    operations = [
        migrations.AddField(
            model_name="consulta",
            name="tele_token",
            field=models.CharField(blank=True, db_index=True, default="", max_length=64),
        ),
    ]
