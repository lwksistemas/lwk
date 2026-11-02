from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("homepage", "0050_nomes_botoes"),
    ]

    operations = [
        migrations.AddField(
            model_name="herosection",
            name="animacoes",
            field=models.JSONField(blank=True, default=dict, help_text="Efeitos visuais da homepage pública. Vazio mantém o visual atual."),
        ),
    ]
