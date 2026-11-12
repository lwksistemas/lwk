from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm_vendas", "0088_conta_nfse_atividade_padrao"),
    ]

    operations = [
        migrations.AddField(
            model_name="crmconfig",
            name="logo_assinatura_tamanho",
            field=models.PositiveSmallIntegerField(
                default=100,
                help_text="Percentual do quadro. 100 preenche o quadro como hoje.",
                verbose_name="Tamanho da logo na assinatura",
            ),
        ),
        migrations.AddField(
            model_name="crmconfig",
            name="logo_assinatura_intensidade",
            field=models.PositiveSmallIntegerField(
                default=25,
                help_text="Opacidade da logo atrás dos dados do cliente e do vendedor.",
                verbose_name="Intensidade da logo na assinatura",
            ),
        ),
    ]
