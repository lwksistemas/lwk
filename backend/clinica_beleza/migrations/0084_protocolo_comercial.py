import django.db.models.deletion
from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0083_recibo_assinatura"),
    ]

    operations = [
        migrations.AddField(
            model_name="procedureprotocol",
            name="sessoes",
            field=models.PositiveIntegerField(default=1, verbose_name="Sessões"),
        ),
        migrations.AddField(
            model_name="procedureprotocol",
            name="intervalo_quantidade",
            field=models.PositiveIntegerField(default=1, verbose_name="Intervalo"),
        ),
        migrations.AddField(
            model_name="procedureprotocol",
            name="intervalo_unidade",
            field=models.CharField(
                choices=[("dias", "Dias"), ("semanas", "Semanas"), ("meses", "Meses")],
                default="dias",
                max_length=10,
                verbose_name="Unidade do intervalo",
            ),
        ),
        migrations.AddField(
            model_name="procedureprotocol",
            name="valor",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0"),
                max_digits=10,
                verbose_name="Valor do protocolo (R$)",
            ),
        ),
        migrations.CreateModel(
            name="ProtocoloProduto",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("quantidade", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Quantidade por sessão")),
                (
                    "produto",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="protocolos",
                        to="clinica_beleza.produtoestoque",
                        verbose_name="Produto",
                    ),
                ),
                (
                    "protocol",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="produtos",
                        to="clinica_beleza.procedureprotocol",
                        verbose_name="Protocolo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Produto do protocolo",
                "verbose_name_plural": "Produtos do protocolo",
                "db_table": "clinica_beleza_protocolo_produto",
                "constraints": [
                    models.UniqueConstraint(fields=("protocol", "produto"), name="cb_protocolo_produto_uniq"),
                ],
            },
        ),
        migrations.CreateModel(
            name="ProtocoloContrato",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                (
                    "forma_cobranca",
                    models.CharField(
                        choices=[("POR_CONSULTA", "Por consulta"), ("TOTAL", "Valor total")],
                        max_length=20,
                        verbose_name="Forma de cobrança",
                    ),
                ),
                ("valor_total", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Valor do protocolo (R$)")),
                ("data_inicio", models.DateTimeField(verbose_name="Primeira sessão")),
                ("sessoes", models.PositiveIntegerField(verbose_name="Sessões")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "local_atendimento",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="protocolos_contratados",
                        to="clinica_beleza.localatendimento",
                        verbose_name="Local de atendimento",
                    ),
                ),
                (
                    "patient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="protocolos_contratados",
                        to="clinica_beleza.patient",
                        verbose_name="Paciente",
                    ),
                ),
                (
                    "professional",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="protocolos_contratados",
                        to="clinica_beleza.professional",
                        verbose_name="Profissional",
                    ),
                ),
                (
                    "protocol",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="contratos",
                        to="clinica_beleza.procedureprotocol",
                        verbose_name="Protocolo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Contrato de protocolo",
                "verbose_name_plural": "Contratos de protocolo",
                "db_table": "clinica_beleza_protocolo_contrato",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddField(
            model_name="appointment",
            name="protocolo_contrato",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="agendamentos",
                to="clinica_beleza.protocolocontrato",
                verbose_name="Contrato do protocolo",
            ),
        ),
        migrations.AddField(
            model_name="appointment",
            name="sessao_numero",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="Sessão do protocolo"),
        ),
    ]
