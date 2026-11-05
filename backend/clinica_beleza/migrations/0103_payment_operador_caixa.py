from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0102_caixa_responsavel"),
    ]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="operador_id",
            field=models.IntegerField(blank=True, null=True, verbose_name="Operador do caixa"),
        ),
        migrations.AddField(
            model_name="payment",
            name="operador_nome",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Quem estava no caixa quando o atendimento foi recebido no PDV.",
                max_length=150,
                verbose_name="Operador do caixa",
            ),
        ),
    ]
