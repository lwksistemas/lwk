from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("clinica_geral", "0005_ficha_prontmed"),
    ]

    operations = [
        migrations.AddField(
            model_name="evolucao",
            name="ficha",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
