# Política de prazo de pagamento por paciente (configurada só pelo admin no prontuário).

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0080_payment_method_despesa"),
    ]

    operations = [
        migrations.AddField(
            model_name="patient",
            name="prazo_pagamento_modo",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "Sem prazo configurado"),
                    ("DIAS_APOS", "Dias após finalizar a consulta"),
                    ("DIA_FIXO", "Dia fixo do mês"),
                ],
                default="",
                help_text=(
                    "Como calcular o vencimento das consultas a prazo deste paciente. "
                    "Vazio = paciente não pode receber a prazo."
                ),
                max_length=20,
                verbose_name="Modo do prazo de pagamento",
            ),
        ),
        migrations.AddField(
            model_name="patient",
            name="prazo_pagamento_dias",
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                help_text="Usado quando o modo é 'Dias após finalizar' (ex.: 10).",
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(365),
                ],
                verbose_name="Dias após finalizar",
            ),
        ),
        migrations.AddField(
            model_name="patient",
            name="prazo_pagamento_dia_mes",
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                help_text="Usado quando o modo é 'Dia fixo do mês' (1 a 28). Vence sempre no mês seguinte.",
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(28),
                ],
                verbose_name="Dia fixo do mês",
            ),
        ),
    ]
