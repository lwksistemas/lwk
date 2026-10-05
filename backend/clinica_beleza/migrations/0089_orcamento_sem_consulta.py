from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0088_remove_consulta_conteudo_termo"),
    ]

    operations = [
        migrations.AlterField(
            model_name="orcamentoconsulta",
            name="consulta",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="orcamentos",
                to="clinica_beleza.consulta",
                verbose_name="Consulta",
            ),
        ),
    ]
