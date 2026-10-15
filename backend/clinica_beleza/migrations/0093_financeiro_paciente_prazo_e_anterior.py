import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0092_cifrar_senhas_issnet"),
    ]

    operations = [
        migrations.CreateModel(
            name="PrazoPagamentoClinica",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("nome", models.CharField(max_length=80, verbose_name="Nome")),
                ("modo", models.CharField(choices=[("DIAS_APOS", "Dias após o lançamento"), ("DIA_FIXO", "Dia fixo do mês"), ("SEMANAL", "Semanal")], max_length=20, verbose_name="Modo")),
                ("dias", models.PositiveSmallIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(365)], verbose_name="Dias")),
                ("dia_mes", models.PositiveSmallIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(28)], verbose_name="Dia do mês")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Prazo de pagamento",
                "verbose_name_plural": "Prazos de pagamento",
                "db_table": "clinica_beleza_prazo_pagamento",
                "ordering": ["nome"],
                "constraints": [models.UniqueConstraint(fields=("loja_id", "nome"), name="uniq_cb_prazo_pagamento_loja_nome")],
            },
        ),
        migrations.AddField(
            model_name="patient",
            name="prazo_opcao",
            field=models.ForeignKey(blank=True, help_text="Prazo criado pelo administrador e aplicado a esta cliente.", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="pacientes", to="clinica_beleza.prazopagamentoclinica", verbose_name="Prazo escolhido"),
        ),
        migrations.CreateModel(
            name="ProcedimentoAnterior",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("data_procedimento", models.DateField(verbose_name="Data do procedimento")),
                ("nome", models.CharField(max_length=200, verbose_name="Procedimento")),
                ("valor", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Valor")),
                ("valor_pago", models.DecimalField(decimal_places=2, default=0, help_text="Entrada recebida antes deste lançamento.", max_digits=10, verbose_name="Já pago")),
                ("data_pagamento", models.DateField(blank=True, help_text="Data em que o valor já pago foi recebido.", null=True, verbose_name="Data do pagamento")),
                ("data_vencimento", models.DateField(blank=True, help_text="Diferença que falta, no vencimento do prazo desta cliente.", null=True, verbose_name="Vencimento da diferença")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("patient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="procedimentos_anteriores", to="clinica_beleza.patient", verbose_name="Paciente")),
            ],
            options={
                "verbose_name": "Procedimento anterior",
                "verbose_name_plural": "Procedimentos anteriores",
                "db_table": "clinica_beleza_procedimento_anterior",
                "ordering": ["-data_procedimento", "-id"],
            },
        ),
        migrations.CreateModel(
            name="ProcedimentoAnteriorRecebimento",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("valor", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Valor recebido")),
                ("data", models.DateField(verbose_name="Data do recebimento")),
                ("payment_method", models.CharField(choices=[("CASH", "Dinheiro"), ("PIX", "PIX"), ("CREDIT_CARD", "Cartão de crédito"), ("DEBIT_CARD", "Cartão de débito"), ("TRANSFER", "Transferência")], max_length=20, verbose_name="Forma de pagamento")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("procedimento", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="recebimentos", to="clinica_beleza.procedimentoanterior", verbose_name="Procedimento")),
            ],
            options={
                "verbose_name": "Recebimento de procedimento anterior",
                "verbose_name_plural": "Recebimentos de procedimentos anteriores",
                "db_table": "clinica_beleza_procedimento_anterior_recebimento",
                "ordering": ["-data", "-id"],
            },
        ),
        migrations.AddIndex(
            model_name="procedimentoanterior",
            index=models.Index(fields=["loja_id", "patient"], name="cb_proc_ant_patient_idx"),
        ),
    ]
