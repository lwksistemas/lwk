from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("superadmin", "0060_loja_colunas_consultas"),
    ]

    operations = [
        migrations.AddField(
            model_name="loja",
            name="colunas_estoque",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Colunas visíveis na listagem de Estoque (clínica). Vazio = todas as colunas padrão.",
            ),
        ),
    ]
