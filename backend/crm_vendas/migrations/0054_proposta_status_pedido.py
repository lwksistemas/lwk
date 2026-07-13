from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm_vendas", "0053_proposta_motivo_cancelamento_contrato_motivo_cancelamento"),
    ]

    operations = [
        migrations.AlterField(
            model_name="proposta",
            name="status",
            field=models.CharField(
                choices=[
                    ("rascunho", "Rascunho"),
                    ("enviada", "Enviada"),
                    ("aceita", "Aceita"),
                    ("pedido", "Pedido"),
                    ("rejeitada", "Rejeitada"),
                    ("cancelada", "Cancelada"),
                ],
                default="rascunho",
                max_length=20,
            ),
        ),
    ]
