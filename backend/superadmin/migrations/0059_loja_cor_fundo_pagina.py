from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("superadmin", "0058_loja_agenda_status_colors"),
    ]

    operations = [
        migrations.AddField(
            model_name="loja",
            name="cor_fundo_pagina",
            field=models.CharField(
                blank=True,
                help_text="Cor de fundo das páginas internas (#RRGGBB). Vazio = tom claro da cor primária.",
                max_length=7,
            ),
        ),
    ]
