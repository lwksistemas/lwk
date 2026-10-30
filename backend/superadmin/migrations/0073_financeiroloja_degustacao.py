from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("superadmin", "0072_credencial_rosto"),
    ]

    operations = [
        migrations.AddField(
            model_name="financeiroloja",
            name="degustacao_ate",
            field=models.DateField(
                blank=True,
                help_text="Último dia de uso sem boleto. Vazio quando a loja não está em demonstração.",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="financeiroloja",
            name="degustacao_avisada",
            field=models.BooleanField(
                default=False,
                help_text="O aviso de fim da demonstração já foi enviado.",
            ),
        ),
        migrations.AlterField(
            model_name="financeiroloja",
            name="status_pagamento",
            field=models.CharField(
                choices=[
                    ("ativo", "Ativo"),
                    ("pendente", "Pagamento Pendente"),
                    ("atrasado", "Atrasado"),
                    ("suspenso", "Suspenso"),
                    ("cancelado", "Cancelado"),
                    ("degustacao", "Demonstração"),
                ],
                default="ativo",
                max_length=20,
            ),
        ),
    ]
