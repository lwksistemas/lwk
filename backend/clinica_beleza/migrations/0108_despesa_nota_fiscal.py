from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0107_simulacao_consulta_historico"),
    ]

    operations = [
        migrations.AddField(
            model_name="despesa",
            name="numero_nota",
            field=models.CharField(blank=True, default="", max_length=20, verbose_name="Número da nota"),
        ),
        migrations.AddField(
            model_name="despesa",
            name="fornecedor_nome",
            field=models.CharField(blank=True, default="", max_length=200, verbose_name="Fornecedor"),
        ),
        migrations.AddField(
            model_name="despesa",
            name="chave_nfe",
            field=models.CharField(blank=True, default="", max_length=44, verbose_name="Chave da NF-e"),
        ),
        migrations.AddField(
            model_name="despesa",
            name="parcela",
            field=models.PositiveSmallIntegerField(default=1, verbose_name="Parcela"),
        ),
        migrations.AddConstraint(
            model_name="despesa",
            constraint=models.UniqueConstraint(
                condition=~models.Q(chave_nfe=""),
                fields=("loja_id", "chave_nfe", "parcela"),
                name="cb_despesa_nfe_parcela_uniq",
            ),
        ),
    ]
