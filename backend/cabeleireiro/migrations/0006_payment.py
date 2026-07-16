import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cabeleireiro", "0005_profissional_comissao"),
    ]

    operations = [
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Valor cobrado")),
                (
                    "valor_total",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=10,
                        null=True,
                        verbose_name="Valor total original",
                    ),
                ),
                (
                    "payment_method",
                    models.CharField(
                        choices=[
                            ("CASH", "Dinheiro"),
                            ("CREDIT_CARD", "Cartão de Crédito"),
                            ("DEBIT_CARD", "Cartão de Débito"),
                            ("PIX", "PIX"),
                            ("TRANSFER", "Transferência"),
                        ],
                        default="CASH",
                        max_length=20,
                        verbose_name="Método de Pagamento",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pendente"),
                            ("PAID", "Pago"),
                            ("CANCELLED", "Cancelado"),
                        ],
                        default="PENDING",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                ("payment_date", models.DateTimeField(blank=True, null=True, verbose_name="Data do Pagamento")),
                ("notes", models.TextField(blank=True, default="", verbose_name="Observações")),
                (
                    "desconto",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0.00"),
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(Decimal("0.00"))],
                        verbose_name="Desconto (R$)",
                    ),
                ),
                (
                    "comissao_percentual",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0.00"),
                        max_digits=5,
                        verbose_name="Comissão %",
                    ),
                ),
                (
                    "comissao_valor",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0.00"),
                        max_digits=10,
                        verbose_name="Comissão R$",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "agendamento",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payments",
                        to="cabeleireiro.agendamento",
                        verbose_name="Agendamento",
                    ),
                ),
            ],
            options={
                "verbose_name": "Pagamento",
                "verbose_name_plural": "Pagamentos",
                "db_table": "cabeleireiro_payment",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["status", "payment_date"], name="cab_pay_status_dt_idx"),
                    models.Index(fields=["agendamento", "status"], name="cab_pay_ag_status_idx"),
                    models.Index(fields=["loja_id", "payment_date"], name="cab_pay_loja_dt_idx"),
                ],
            },
        ),
    ]
