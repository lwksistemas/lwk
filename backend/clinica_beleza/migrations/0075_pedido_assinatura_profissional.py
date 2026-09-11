from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0074_fornecedor_pedido_compra"),
    ]

    operations = [
        migrations.AddField(
            model_name="pedidocompraassinatura",
            name="conselho_display",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
        migrations.AddField(
            model_name="pedidocompraassinatura",
            name="cpf_assinante",
            field=models.CharField(blank=True, default="", max_length=14),
        ),
        migrations.AddField(
            model_name="pedidocompraassinatura",
            name="profissional",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="assinaturas_pedido_compra",
                to="clinica_beleza.professional",
            ),
        ),
    ]
