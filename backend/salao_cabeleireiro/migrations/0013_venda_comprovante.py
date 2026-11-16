from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("salao_cabeleireiro", "0012_sessao_caixa_operador"),
    ]

    operations = [
        migrations.AddField(
            model_name="venda",
            name="comprovante",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
