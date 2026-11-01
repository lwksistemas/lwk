from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("homepage", "0048_letra_home"),
    ]

    operations = [
        migrations.AddField(
            model_name="paginasite",
            name="imagem",
            field=models.URLField(blank=True, default="", help_text="Foto do cartão na home. Vazio mantém a imagem atual.", max_length=500),
        ),
    ]
