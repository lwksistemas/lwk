from django.db import migrations, models


_CHOICES = [
    ("CASH", "Dinheiro"),
    ("CREDIT_CARD", "Cartão de Crédito"),
    ("DEBIT_CARD", "Cartão de Débito"),
    ("PIX", "PIX"),
    ("TRANSFER", "Transferência"),
    ("PRAZO", "A prazo"),
    ("DESPESA", "Despesa (clínica)"),
]


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0079_categoria_procedimento"),
    ]

    operations = [
        migrations.AlterField(
            model_name="payment",
            name="payment_method",
            field=models.CharField(
                choices=_CHOICES,
                max_length=20,
                verbose_name="Método de Pagamento",
            ),
        ),
        migrations.AlterField(
            model_name="paymentparcela",
            name="payment_method",
            field=models.CharField(
                choices=_CHOICES,
                max_length=20,
                verbose_name="Forma de pagamento",
            ),
        ),
        migrations.AlterField(
            model_name="despesa",
            name="forma_pagamento",
            field=models.CharField(
                blank=True,
                choices=_CHOICES,
                default="",
                max_length=20,
                verbose_name="Forma de pagamento",
            ),
        ),
    ]
