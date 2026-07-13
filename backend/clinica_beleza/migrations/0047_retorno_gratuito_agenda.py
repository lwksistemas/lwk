
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0046_professional_tempo_consulta"),
    ]

    operations = [
        migrations.CreateModel(
            name="AgendaRetornoConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True)),
                ("retorno_procedimento_ativo", models.BooleanField(default=False, help_text="Isenta taxa de consulta quando o paciente retorna para acompanhamento do procedimento.", verbose_name="Retorno por procedimento ativo")),
                ("retorno_consulta_ativo", models.BooleanField(default=False, help_text="Isenta taxa de consulta quando o paciente teve consulta concluída dentro do prazo.", verbose_name="Retorno por consulta ativo")),
                ("dias_retorno_consulta", models.PositiveIntegerField(default=30, verbose_name="Prazo retorno por consulta (dias)")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Configuração de retorno da agenda",
                "verbose_name_plural": "Configurações de retorno da agenda",
                "db_table": "clinica_beleza_agenda_retorno_config",
            },
        ),
        migrations.CreateModel(
            name="RetornoProcedimentoRegra",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True)),
                ("dias_retorno", models.PositiveIntegerField(help_text="Dias após o procedimento concluído em que a taxa de consulta não é cobrada.", verbose_name="Prazo (dias)")),
                ("is_active", models.BooleanField(default=True, verbose_name="Ativo")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("procedure", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="regras_retorno", to="clinica_beleza.procedure", verbose_name="Procedimento")),
            ],
            options={
                "verbose_name": "Regra de retorno por procedimento",
                "verbose_name_plural": "Regras de retorno por procedimento",
                "db_table": "clinica_beleza_retorno_procedimento_regra",
                "ordering": ["procedure__nome"],
            },
        ),
        migrations.AddConstraint(
            model_name="retornoprocedimentoregra",
            constraint=models.UniqueConstraint(fields=("procedure", "loja_id"), name="uniq_retorno_procedimento_loja"),
        ),
        migrations.AddField(
            model_name="appointment",
            name="retorno_procedure",
            field=models.ForeignKey(blank=True, help_text="Indica retorno de acompanhamento deste procedimento (sem repetir cobrança da consulta).", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="agendamentos_retorno", to="clinica_beleza.procedure", verbose_name="Retorno do procedimento"),
        ),
        migrations.AddField(
            model_name="consulta",
            name="retorno_gratuito",
            field=models.BooleanField(default=False, help_text="Taxa de consulta isenta por retorno dentro do prazo configurado.", verbose_name="Retorno gratuito"),
        ),
        migrations.AddField(
            model_name="consulta",
            name="retorno_tipo",
            field=models.CharField(blank=True, choices=[("", "—"), ("procedimento", "Por procedimento"), ("consulta", "Por consulta")], default="", max_length=20, verbose_name="Tipo de retorno"),
        ),
    ]
