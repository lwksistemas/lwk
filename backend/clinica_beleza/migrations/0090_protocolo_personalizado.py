import django.db.models.deletion
from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0089_orcamento_sem_consulta"),
    ]

    operations = [
        migrations.AlterField(
            model_name="protocolocontrato",
            name="protocol",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="contratos",
                to="clinica_beleza.procedureprotocol",
                verbose_name="Protocolo",
            ),
        ),
        migrations.AddField(
            model_name="protocolocontrato",
            name="nome",
            field=models.CharField(blank=True, default="", max_length=200, verbose_name="Nome do tratamento"),
        ),
        migrations.AddField(
            model_name="protocolocontrato",
            name="valor_bruto",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                max_digits=10,
                verbose_name="Soma dos procedimentos (R$)",
            ),
        ),
        migrations.AddField(
            model_name="protocolocontrato",
            name="desconto_tipo",
            field=models.CharField(
                blank=True,
                choices=[("", "—"), ("fixo", "Valor fixo"), ("percentual", "Porcentagem")],
                default="",
                max_length=20,
                verbose_name="Tipo de desconto",
            ),
        ),
        migrations.AddField(
            model_name="protocolocontrato",
            name="desconto_valor",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                max_digits=10,
                verbose_name="Desconto informado",
            ),
        ),
        migrations.AddField(
            model_name="protocolocontrato",
            name="tempo_minutos",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                verbose_name="Duração de cada atendimento (min)",
            ),
        ),
        migrations.AddField(
            model_name="protocolocontrato",
            name="intervalo_quantidade",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="Intervalo"),
        ),
        migrations.AddField(
            model_name="protocolocontrato",
            name="intervalo_unidade",
            field=models.CharField(blank=True, default="", max_length=10, verbose_name="Unidade do intervalo"),
        ),
        migrations.CreateModel(
            name="ProtocoloContratoProcedimento",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("valor", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Valor no pacote (R$)")),
                (
                    "contrato",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="procedimentos",
                        to="clinica_beleza.protocolocontrato",
                        verbose_name="Contrato",
                    ),
                ),
                (
                    "procedure",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="protocolos_personalizados",
                        to="clinica_beleza.procedure",
                        verbose_name="Procedimento",
                    ),
                ),
            ],
            options={
                "verbose_name": "Procedimento do protocolo personalizado",
                "verbose_name_plural": "Procedimentos do protocolo personalizado",
                "db_table": "clinica_beleza_protocolo_contrato_procedimento",
            },
        ),
        migrations.CreateModel(
            name="ProtocoloContratoProduto",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                (
                    "quantidade",
                    models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Quantidade por sessão"),
                ),
                (
                    "contrato",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="produtos_sessao",
                        to="clinica_beleza.protocolocontrato",
                        verbose_name="Contrato",
                    ),
                ),
                (
                    "produto",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="protocolos_personalizados",
                        to="clinica_beleza.produtoestoque",
                        verbose_name="Produto",
                    ),
                ),
            ],
            options={
                "verbose_name": "Produto do protocolo personalizado",
                "verbose_name_plural": "Produtos do protocolo personalizado",
                "db_table": "clinica_beleza_protocolo_contrato_produto",
            },
        ),
        migrations.AddConstraint(
            model_name="protocolocontratoprocedimento",
            constraint=models.UniqueConstraint(
                fields=("contrato", "procedure"),
                name="cb_protocolo_contrato_proc_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="protocolocontratoproduto",
            constraint=models.UniqueConstraint(
                fields=("contrato", "produto"),
                name="cb_protocolo_contrato_produto_uniq",
            ),
        ),
    ]
