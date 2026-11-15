from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("salao_cabeleireiro", "0003_comunicacao_whatsapp"),
    ]

    operations = [
        migrations.AddField(
            model_name="recebimento",
            name="partes",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
