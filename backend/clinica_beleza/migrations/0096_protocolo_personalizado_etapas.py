from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0095_protocolo_personalizado_desconto"),
    ]

    operations = [
        migrations.AddField(
            model_name="protocolocontrato",
            name="materiais_necessarios",
            field=models.TextField(blank=True, default="", verbose_name="Materiais necessários"),
        ),
        migrations.AddField(
            model_name="protocolocontrato",
            name="preparacao",
            field=models.TextField(blank=True, default="", verbose_name="Preparação"),
        ),
        migrations.AddField(
            model_name="protocolocontrato",
            name="execucao",
            field=models.TextField(blank=True, default="", verbose_name="Execução (passos)"),
        ),
        migrations.AddField(
            model_name="protocolocontrato",
            name="pos_procedimento",
            field=models.TextField(blank=True, default="", verbose_name="Pós-procedimento"),
        ),
        migrations.AddField(
            model_name="protocolocontrato",
            name="contraindicacoes",
            field=models.TextField(blank=True, default="", verbose_name="Contraindicações"),
        ),
        migrations.AddField(
            model_name="protocolocontrato",
            name="cuidados_especiais",
            field=models.TextField(blank=True, default="", verbose_name="Cuidados especiais"),
        ),
    ]
