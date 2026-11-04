from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0101_venda_sem_cliente"),
    ]

    operations = [
        migrations.AddField(
            model_name="sessaocaixa",
            name="nome",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
        migrations.AddField(
            model_name="sessaocaixa",
            name="responsavel_id",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="sessaocaixa",
            name="responsavel_nome",
            field=models.CharField(blank=True, default="", max_length=150),
        ),
    ]
