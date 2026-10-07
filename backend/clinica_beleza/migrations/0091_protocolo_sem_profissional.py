import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0090_protocolo_personalizado"),
    ]

    operations = [
        migrations.AlterField(
            model_name="protocolocontrato",
            name="professional",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="protocolos_contratados",
                to="clinica_beleza.professional",
                verbose_name="Profissional",
            ),
        ),
        migrations.AlterField(
            model_name="protocolocontrato",
            name="forma_cobranca",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "A definir"),
                    ("POR_CONSULTA", "Por consulta"),
                    ("TOTAL", "Valor total"),
                ],
                default="",
                max_length=20,
                verbose_name="Forma de cobrança",
            ),
        ),
        migrations.AlterField(
            model_name="protocolocontrato",
            name="data_inicio",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Primeira sessão"),
        ),
    ]
