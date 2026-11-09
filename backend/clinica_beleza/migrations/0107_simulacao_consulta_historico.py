from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0106_simulacao_consulta"),
    ]

    operations = [
        migrations.AddField(
            model_name="simulacaoconsulta",
            name="api_nome",
            field=models.CharField(blank=True, default="Perfect Corp YouCam", max_length=80),
        ),
        migrations.AddField(
            model_name="simulacaoconsulta",
            name="endpoint",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
        migrations.AddField(
            model_name="simulacaoconsulta",
            name="pedido",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="simulacaoconsulta",
            name="profissional_nome",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="simulacaoconsulta",
            name="procedimento_nome",
            field=models.CharField(blank=True, default="", max_length=300),
        ),
        migrations.AddField(
            model_name="simulacaoconsulta",
            name="unidades",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="simulacaoconsulta",
            name="unidades_fonte",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
    ]
