from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("homepage", "0049_foto_solucoes"),
    ]

    operations = [
        migrations.AddField(
            model_name="herosection",
            name="rotulos_botoes",
            field=models.JSONField(blank=True, default=dict, help_text="Nomes dos botões da home. Vazio usa o texto padrão."),
        ),
    ]
