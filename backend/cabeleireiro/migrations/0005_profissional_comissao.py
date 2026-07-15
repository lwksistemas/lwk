import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cabeleireiro", "0004_categoria_e_horarios"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProfissionalComissao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                (
                    "modo",
                    models.CharField(
                        choices=[("percentual", "Percentual (%)"), ("fixo", "Valor fixo (R$)")],
                        default="percentual",
                        max_length=15,
                        verbose_name="Modo de cálculo",
                    ),
                ),
                (
                    "valor",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0.00"),
                        help_text="Percentual (ex: 40.00 = 40%) ou valor fixo em R$.",
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(Decimal("0.00"))],
                        verbose_name="Valor",
                    ),
                ),
                ("is_active", models.BooleanField(default=True, verbose_name="Ativo")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "categoria",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="comissoes",
                        to="cabeleireiro.categoriaservico",
                        verbose_name="Categoria de serviço",
                    ),
                ),
                (
                    "profissional",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="comissoes",
                        to="cabeleireiro.profissional",
                        verbose_name="Profissional",
                    ),
                ),
            ],
            options={
                "verbose_name": "Comissão do profissional",
                "verbose_name_plural": "Comissões dos profissionais",
                "db_table": "cabeleireiro_profissionalcomissao",
                "ordering": ["profissional", "categoria"],
                "indexes": [
                    models.Index(fields=["loja_id", "profissional", "is_active"], name="cab_com_loja_prof_idx"),
                    models.Index(fields=["profissional", "categoria"], name="cab_com_prof_cat_idx"),
                ],
            },
        ),
    ]
