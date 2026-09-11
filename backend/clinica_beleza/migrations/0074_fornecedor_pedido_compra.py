from decimal import Decimal

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0073_patient_sexo"),
    ]

    operations = [
        migrations.CreateModel(
            name="Fornecedor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True)),
                ("cnpj", models.CharField(max_length=18, verbose_name="CNPJ")),
                ("razao_social", models.CharField(max_length=200, verbose_name="Razão social")),
                ("nome_fantasia", models.CharField(blank=True, default="", max_length=200)),
                ("inscricao_estadual", models.CharField(blank=True, default="", max_length=30)),
                ("email", models.EmailField(blank=True, default="", max_length=254)),
                ("telefone", models.CharField(blank=True, default="", max_length=20)),
                ("cep", models.CharField(blank=True, default="", max_length=10)),
                ("logradouro", models.CharField(blank=True, default="", max_length=200)),
                ("numero", models.CharField(blank=True, default="", max_length=20)),
                ("complemento", models.CharField(blank=True, default="", max_length=100)),
                ("bairro", models.CharField(blank=True, default="", max_length=100)),
                ("municipio", models.CharField(blank=True, default="", max_length=100)),
                ("uf", models.CharField(blank=True, default="", max_length=2)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Fornecedor",
                "verbose_name_plural": "Fornecedores",
                "db_table": "clinica_beleza_fornecedor",
                "ordering": ["razao_social"],
            },
        ),
        migrations.CreateModel(
            name="FornecedorProduto",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True)),
                ("codigo", models.CharField(max_length=60)),
                ("nome", models.CharField(max_length=200)),
                ("unidade", models.CharField(blank=True, default="un", max_length=20)),
                ("preco_ref", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "fornecedor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="produtos",
                        to="clinica_beleza.fornecedor",
                    ),
                ),
            ],
            options={
                "db_table": "clinica_beleza_fornecedor_produto",
                "ordering": ["nome"],
            },
        ),
        migrations.CreateModel(
            name="PedidoCompra",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True)),
                ("numero", models.PositiveIntegerField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("rascunho", "Rascunho"),
                            ("aguardando_fornecedor", "Aguardando fornecedor"),
                            ("assinado", "Assinado"),
                            ("enviado", "Enviado"),
                            ("cancelado", "Cancelado"),
                        ],
                        default="rascunho",
                        max_length=30,
                    ),
                ),
                ("observacoes", models.TextField(blank=True, default="")),
                ("pdf_url", models.URLField(blank=True, default="", max_length=500)),
                ("valor_total", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "fornecedor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="pedidos",
                        to="clinica_beleza.fornecedor",
                    ),
                ),
            ],
            options={
                "db_table": "clinica_beleza_pedido_compra",
                "ordering": ["-numero"],
            },
        ),
        migrations.CreateModel(
            name="PedidoCompraItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("codigo", models.CharField(max_length=60)),
                ("nome", models.CharField(max_length=200)),
                ("unidade", models.CharField(blank=True, default="un", max_length=20)),
                ("quantidade", models.DecimalField(decimal_places=2, default=Decimal("1"), max_digits=10)),
                ("preco", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10)),
                (
                    "catalogo",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="clinica_beleza.fornecedorproduto",
                    ),
                ),
                (
                    "pedido",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="itens",
                        to="clinica_beleza.pedidocompra",
                    ),
                ),
            ],
            options={
                "db_table": "clinica_beleza_pedido_compra_item",
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="PedidoCompraAssinatura",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True)),
                ("tipo", models.CharField(choices=[("clinica", "Clínica"), ("fornecedor", "Fornecedor")], max_length=15)),
                ("nome_assinante", models.CharField(blank=True, default="", max_length=200)),
                ("email_assinante", models.EmailField(blank=True, default="", max_length=254)),
                ("ip_address", models.GenericIPAddressField(default="0.0.0.0")),
                ("token", models.CharField(blank=True, db_index=True, default="", max_length=512)),
                ("assinado", models.BooleanField(default=False)),
                ("assinado_em", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "pedido",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assinaturas",
                        to="clinica_beleza.pedidocompra",
                    ),
                ),
            ],
            options={
                "db_table": "clinica_beleza_pedido_assinatura",
            },
        ),
        migrations.AddIndex(
            model_name="fornecedor",
            index=models.Index(fields=["loja_id", "cnpj"], name="cb_forn_loja_cnpj_idx"),
        ),
        migrations.AddConstraint(
            model_name="fornecedorproduto",
            constraint=models.UniqueConstraint(fields=("fornecedor", "codigo"), name="cb_forn_prod_codigo_uniq"),
        ),
        migrations.AddConstraint(
            model_name="pedidocompra",
            constraint=models.UniqueConstraint(fields=("loja_id", "numero"), name="cb_pedido_loja_num_uniq"),
        ),
        migrations.AddIndex(
            model_name="pedidocompraassinatura",
            index=models.Index(fields=["pedido", "tipo"], name="cb_pedido_ass_tipo_idx"),
        ),
    ]
