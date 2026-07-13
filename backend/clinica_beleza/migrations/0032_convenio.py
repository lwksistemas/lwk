# Generated manually

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0031_professional_commission_local"),
    ]

    operations = [
        migrations.CreateModel(
            name="Convenio",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, verbose_name="Loja")),
                ("nome", models.CharField(max_length=200, verbose_name="Nome")),
                ("codigo", models.CharField(blank=True, default="", max_length=50, verbose_name="Código")),
                ("is_active", models.BooleanField(default=True, verbose_name="Ativo")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Convênio",
                "verbose_name_plural": "Convênios",
                "db_table": "clinica_beleza_convenios",
                "ordering": ["nome"],
            },
        ),
        migrations.CreateModel(
            name="ConvenioProcedimentoPreco",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, verbose_name="Loja")),
                ("preco", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Preço (R$)")),
                ("is_active", models.BooleanField(default=True, verbose_name="Ativo")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("convenio", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="precos_procedimentos", to="clinica_beleza.convenio", verbose_name="Convênio")),
                ("procedure", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="precos_convenio", to="clinica_beleza.procedure", verbose_name="Procedimento")),
            ],
            options={
                "verbose_name": "Preço convênio × procedimento",
                "verbose_name_plural": "Preços convênio × procedimento",
                "db_table": "clinica_beleza_convenio_procedimento_precos",
                "ordering": ["convenio", "procedure__nome"],
            },
        ),
        migrations.AddField(
            model_name="patient",
            name="convenio",
            field=models.ForeignKey(blank=True, help_text="Convênio sugerido ao agendar ou abrir consulta.", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="pacientes", to="clinica_beleza.convenio", verbose_name="Convênio padrão"),
        ),
        migrations.AddField(
            model_name="appointment",
            name="convenio",
            field=models.ForeignKey(blank=True, help_text="Convênio do atendimento (define preços dos procedimentos).", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="agendamentos", to="clinica_beleza.convenio", verbose_name="Convênio"),
        ),
        migrations.AddField(
            model_name="consulta",
            name="convenio",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="consultas", to="clinica_beleza.convenio", verbose_name="Convênio"),
        ),
        migrations.AddConstraint(
            model_name="convenioprocedimentopreco",
            constraint=models.UniqueConstraint(fields=("convenio", "procedure", "loja_id"), name="uniq_convenio_procedure_loja"),
        ),
    ]
