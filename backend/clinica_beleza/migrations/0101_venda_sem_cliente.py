import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0100_venda_produto"),
    ]

    operations = [
        migrations.CreateModel(
            name="SessaoCaixa",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, verbose_name="Loja")),
                ("operador_id", models.IntegerField(blank=True, null=True)),
                ("operador_nome", models.CharField(blank=True, default="", max_length=150)),
                ("status", models.CharField(choices=[("aberta", "Aberta"), ("fechada", "Fechada")], default="aberta", max_length=10)),
                ("aberta_em", models.DateTimeField(auto_now_add=True)),
                ("fechada_em", models.DateTimeField(blank=True, null=True)),
            ],
            options={"ordering": ["-aberta_em"]},
        ),
        migrations.AddField(
            model_name="vendabalcao",
            name="nome_cliente",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="vendabalcao",
            name="telefone_cliente",
            field=models.CharField(blank=True, default="", max_length=30),
        ),
        migrations.AddField(
            model_name="vendabalcao",
            name="email_cliente",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="vendabalcao",
            name="operador_id",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="vendabalcao",
            name="operador_nome",
            field=models.CharField(blank=True, default="", max_length=150),
        ),
        migrations.AddField(
            model_name="vendabalcao",
            name="chave",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="vendabalcao",
            name="sessao",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="vendas", to="clinica_beleza.sessaocaixa"),
        ),
        migrations.AlterField(
            model_name="vendabalcao",
            name="paciente",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="vendas_balcao", to="clinica_beleza.patient", verbose_name="Cliente"),
        ),
        migrations.AddConstraint(
            model_name="vendabalcao",
            constraint=models.UniqueConstraint(condition=models.Q(("chave", ""), _negated=True), fields=("loja_id", "chave"), name="cb_venda_balcao_chave"),
        ),
    ]
