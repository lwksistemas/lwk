from decimal import Decimal

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("salao_cabeleireiro", "0006_funcionamento"),
    ]

    operations = [
        migrations.CreateModel(
            name="Produto",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True)),
                ("nome", models.CharField(max_length=120)),
                ("codigo_barras", models.CharField(blank=True, default="", max_length=40)),
                ("preco", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=10)),
                ("saldo", models.PositiveIntegerField(default=0)),
                ("comissao_percentual", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=5)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"verbose_name": "Produto", "ordering": ["nome"]},
        ),
        migrations.CreateModel(
            name="Venda",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True)),
                ("numero", models.PositiveIntegerField()),
                ("cliente_nome", models.CharField(blank=True, default="", max_length=160)),
                ("valor_servico", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=10)),
                ("valor_produtos", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=10)),
                ("desconto", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=10)),
                ("valor", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=10)),
                ("forma", models.CharField(choices=[("dinheiro", "Dinheiro"), ("pix", "Pix"), ("debito", "Débito"), ("credito", "Crédito")], default="dinheiro", max_length=20)),
                ("partes", models.JSONField(blank=True, default=list)),
                ("partes_produtos", models.JSONField(blank=True, default=list)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("agendamento", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="vendas", to="salao_cabeleireiro.agendamento")),
                ("recebimento", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="vendas", to="salao_cabeleireiro.recebimento")),
            ],
            options={"verbose_name": "Venda do caixa", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="VendaItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(max_length=120)),
                ("quantidade", models.PositiveIntegerField()),
                ("preco", models.DecimalField(decimal_places=2, max_digits=10)),
                ("total", models.DecimalField(decimal_places=2, max_digits=10)),
                ("comissao_valor", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=10)),
                ("estoque_baixado", models.BooleanField(default=False)),
                ("produto", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="itens", to="salao_cabeleireiro.produto")),
                ("venda", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="itens", to="salao_cabeleireiro.venda")),
            ],
            options={"verbose_name": "Item da venda"},
        ),
        migrations.CreateModel(
            name="MovimentoEstoque",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tipo", models.CharField(max_length=20)),
                ("quantidade", models.IntegerField()),
                ("saldo_depois", models.PositiveIntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("produto", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="movimentos", to="salao_cabeleireiro.produto")),
                ("venda", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="movimentos", to="salao_cabeleireiro.venda")),
            ],
            options={"verbose_name": "Movimento de estoque", "ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="produto",
            constraint=models.UniqueConstraint(condition=~models.Q(codigo_barras="") & models.Q(is_active=True), fields=("loja_id", "codigo_barras"), name="salao_produto_codigo_ativo"),
        ),
    ]
