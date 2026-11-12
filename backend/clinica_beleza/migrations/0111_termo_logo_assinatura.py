from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0110_recebimento_anterior_quem_recebeu"),
    ]

    operations = [
        migrations.AddField(
            model_name="termoconsentimentoconfig",
            name="logo_assinatura_tamanho",
            field=models.PositiveSmallIntegerField(
                default=100,
                help_text="Percentual do quadro. 100 mantém o tamanho atual.",
                verbose_name="Tamanho da logo na assinatura",
            ),
        ),
        migrations.AddField(
            model_name="termoconsentimentoconfig",
            name="logo_assinatura_intensidade",
            field=models.PositiveSmallIntegerField(
                default=55,
                help_text="Opacidade da logo atrás dos dados do paciente e do profissional.",
                verbose_name="Intensidade da logo na assinatura",
            ),
        ),
    ]
