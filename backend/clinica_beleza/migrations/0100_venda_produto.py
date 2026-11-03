import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0099_compra_fornecedor_e_lote"),
    ]

    operations = [
        migrations.AddField(
            model_name="produtoestoque",
            name="vende_ao_cliente",
            field=models.BooleanField(
                default=False,
                help_text="Insumo de procedimento continua só baixando o estoque. Só o marcado aqui entra no recibo.",
                verbose_name="Pode vender ao cliente",
            ),
        ),
        migrations.AddField(
            model_name="consultaprodutoutilizado",
            name="finalidade",
            field=models.CharField(
                choices=[("uso", "Utilizado no procedimento"), ("venda", "Vendido ao cliente")],
                default="uso",
                max_length=10,
                verbose_name="Finalidade",
            ),
        ),
        migrations.AddField(
            model_name="consultaprodutoutilizado",
            name="preco_unitario",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name="Preço unitário de venda"),
        ),
        migrations.AddField(
            model_name="consultaprodutoutilizado",
            name="desconto",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name="Desconto da linha (R$)"),
        ),
        migrations.AddField(
            model_name="consultaprodutoutilizado",
            name="estornado",
            field=models.BooleanField(default=False, verbose_name="Venda estornada"),
        ),
        migrations.AddField(
            model_name="payment",
            name="valor_produtos",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Parte do total que é venda de produto. Serviço continua no restante.",
                max_digits=10,
                verbose_name="Receita de produtos (R$)",
            ),
        ),
        migrations.AlterField(
            model_name="payment",
            name="appointment",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="clinica_beleza.appointment",
                verbose_name="Agendamento",
            ),
        ),
        migrations.CreateModel(
            name="VendaBalcao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, verbose_name="Loja")),
                ("status", models.CharField(choices=[("concluida", "Concluída"), ("cancelada", "Cancelada")], default="concluida", max_length=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("paciente", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="vendas_balcao", to="clinica_beleza.patient", verbose_name="Cliente")),
                ("payment", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="venda_balcao", to="clinica_beleza.payment")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="VendaBalcaoItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, verbose_name="Loja")),
                ("quantidade", models.DecimalField(decimal_places=2, max_digits=10)),
                ("preco_unitario", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("desconto", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("estoque_baixado", models.BooleanField(default=False)),
                ("estornado", models.BooleanField(default=False)),
                ("produto", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="vendas_balcao", to="clinica_beleza.produtoestoque")),
                ("venda", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="itens", to="clinica_beleza.vendabalcao")),
            ],
        ),
    ]
