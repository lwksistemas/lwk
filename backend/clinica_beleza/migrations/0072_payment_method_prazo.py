from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0071_professional_foto_url"),
    ]

    operations = [
        migrations.AlterField(
            model_name="payment",
            name="payment_method",
            field=models.CharField(
                choices=[
                    ("CASH", "Dinheiro"),
                    ("CREDIT_CARD", "Cartão de Crédito"),
                    ("DEBIT_CARD", "Cartão de Débito"),
                    ("PIX", "PIX"),
                    ("TRANSFER", "Transferência"),
                    ("PRAZO", "A prazo"),
                ],
                max_length=20,
                verbose_name="Método de Pagamento",
            ),
        ),
        migrations.AlterField(
            model_name="paymentparcela",
            name="payment_method",
            field=models.CharField(
                choices=[
                    ("CASH", "Dinheiro"),
                    ("CREDIT_CARD", "Cartão de Crédito"),
                    ("DEBIT_CARD", "Cartão de Débito"),
                    ("PIX", "PIX"),
                    ("TRANSFER", "Transferência"),
                    ("PRAZO", "A prazo"),
                ],
                max_length=20,
                verbose_name="Forma de pagamento",
            ),
        ),
        migrations.AlterField(
            model_name="despesa",
            name="forma_pagamento",
            field=models.CharField(
                blank=True,
                choices=[
                    ("CASH", "Dinheiro"),
                    ("CREDIT_CARD", "Cartão de Crédito"),
                    ("DEBIT_CARD", "Cartão de Débito"),
                    ("PIX", "PIX"),
                    ("TRANSFER", "Transferência"),
                    ("PRAZO", "A prazo"),
                ],
                default="",
                max_length=20,
                verbose_name="Forma de pagamento",
            ),
        ),
    ]
