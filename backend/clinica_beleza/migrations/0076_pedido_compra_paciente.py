from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0075_pedido_assinatura_profissional"),
    ]

    operations = [
        migrations.CreateModel(
            name="PedidoCompraPaciente",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(max_length=200)),
                ("cpf", models.CharField(blank=True, default="", max_length=14)),
                (
                    "patient",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="pedidos_compra",
                        to="clinica_beleza.patient",
                    ),
                ),
                (
                    "pedido",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pacientes",
                        to="clinica_beleza.pedidocompra",
                    ),
                ),
            ],
            options={
                "db_table": "clinica_beleza_pedido_compra_paciente",
                "ordering": ["id"],
            },
        ),
    ]
