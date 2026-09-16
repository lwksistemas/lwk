from decimal import Decimal

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0076_pedido_compra_paciente"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrcamentoConsulta",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("observacoes", models.TextField(blank=True, default="", verbose_name="Observações")),
                (
                    "valor_total",
                    models.DecimalField(
                        decimal_places=2, default=Decimal("0.00"), max_digits=10, verbose_name="Valor Total",
                    ),
                ),
                ("validade_dias", models.PositiveIntegerField(default=30, verbose_name="Validade (dias)")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("RASCUNHO", "Rascunho"),
                            ("ENVIADO", "Enviado"),
                            ("ACEITO", "Aceito"),
                            ("RECUSADO", "Recusado"),
                        ],
                        default="RASCUNHO",
                        max_length=20,
                    ),
                ),
                ("enviado_email", models.BooleanField(default=False)),
                ("enviado_whatsapp", models.BooleanField(default=False)),
                ("data_envio", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "consulta",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="orcamentos",
                        to="clinica_beleza.consulta",
                        verbose_name="Consulta",
                    ),
                ),
                (
                    "patient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="orcamentos",
                        to="clinica_beleza.patient",
                        verbose_name="Paciente",
                    ),
                ),
                (
                    "professional",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="orcamentos",
                        to="clinica_beleza.professional",
                        verbose_name="Profissional",
                    ),
                ),
            ],
            options={
                "verbose_name": "Orçamento",
                "verbose_name_plural": "Orçamentos",
                "db_table": "clinica_beleza_orcamento_consulta",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="OrcamentoItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome_procedimento", models.CharField(max_length=200, verbose_name="Procedimento")),
                ("descricao_procedimento", models.TextField(blank=True, default="")),
                (
                    "valor_original",
                    models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Valor Original"),
                ),
                (
                    "valor_customizado",
                    models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Valor Orçado"),
                ),
                ("quantidade", models.PositiveIntegerField(default=1, verbose_name="Quantidade")),
                ("observacao_item", models.TextField(blank=True, default="", verbose_name="Observação")),
                (
                    "orcamento",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="itens",
                        to="clinica_beleza.orcamentoconsulta",
                    ),
                ),
                (
                    "procedure",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="clinica_beleza.procedure",
                    ),
                ),
            ],
            options={
                "db_table": "clinica_beleza_orcamento_item",
                "ordering": ["id"],
            },
        ),
    ]
