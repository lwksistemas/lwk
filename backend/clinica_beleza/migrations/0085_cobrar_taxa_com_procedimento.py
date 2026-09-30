from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0084_protocolo_comercial"),
    ]

    operations = [
        migrations.AddField(
            model_name="agendaretornoconfig",
            name="cobrar_taxa_com_procedimento",
            field=models.BooleanField(
                default=True,
                help_text=(
                    "Marcado: a taxa do local entra no atendimento que tem procedimento. "
                    "Desmarcado: o recibo mostra só o procedimento; consulta sem procedimento "
                    "continua com a taxa. O retorno gratuito da visita seguinte não muda."
                ),
                verbose_name="Cobrar taxa de consulta junto com o procedimento",
            ),
        ),
    ]
