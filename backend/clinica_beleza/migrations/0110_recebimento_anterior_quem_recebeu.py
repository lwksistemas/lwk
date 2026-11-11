from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0109_vinculo_uso_consumo"),
    ]

    operations = [
        migrations.AddField(
            model_name="procedimentoanteriorrecebimento",
            name="recebido_por_id",
            field=models.IntegerField(blank=True, null=True, verbose_name="Quem recebeu"),
        ),
        migrations.AddField(
            model_name="procedimentoanteriorrecebimento",
            name="recebido_por_nome",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Usuário logado que confirmou este recebimento.",
                max_length=150,
                verbose_name="Quem recebeu",
            ),
        ),
    ]
