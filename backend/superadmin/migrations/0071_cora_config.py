from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("superadmin", "0070_loja_colunas_pacientes"),
    ]

    operations = [
        migrations.CreateModel(
            name="CoraConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("singleton_key", models.CharField(default="config", max_length=10, unique=True)),
                ("client_id", models.CharField(blank=True, max_length=80)),
                ("certificate_pem", models.TextField(blank=True)),
                ("private_key_pem", models.TextField(blank=True)),
                ("enabled", models.BooleanField(default=False)),
                ("use_for_boletos", models.BooleanField(default=False, help_text="Se ativo, novas lojas nascem com boleto da Cora.")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Configuração Cora",
                "db_table": "superadmin_cora_config",
            },
        ),
        migrations.AddField(
            model_name="financeiroloja",
            name="cora_invoice_id",
            field=models.CharField(blank=True, help_text="ID da fatura na Cora", max_length=80),
        ),
        migrations.AddField(
            model_name="pagamentoloja",
            name="cora_invoice_id",
            field=models.CharField(blank=True, help_text="ID da fatura na Cora", max_length=80),
        ),
        migrations.AlterField(
            model_name="loja",
            name="provedor_boleto_preferido",
            field=models.CharField(
                choices=[("asaas", "Asaas"), ("mercadopago", "Mercado Pago"), ("cora", "Cora")],
                default="asaas",
                help_text="Provedor de boleto a usar nas cobranças desta loja",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="financeiroloja",
            name="provedor_boleto",
            field=models.CharField(
                choices=[("asaas", "Asaas"), ("mercadopago", "Mercado Pago"), ("cora", "Cora")],
                default="asaas",
                help_text="Provedor usado para gerar boleto desta cobrança",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="pagamentoloja",
            name="provedor_boleto",
            field=models.CharField(
                choices=[("asaas", "Asaas"), ("mercadopago", "Mercado Pago"), ("cora", "Cora")],
                default="asaas",
                help_text="Provedor do boleto (Asaas ou Mercado Pago)",
                max_length=20,
            ),
        ),
    ]
