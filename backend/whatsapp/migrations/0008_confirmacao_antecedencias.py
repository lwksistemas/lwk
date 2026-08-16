from django.db import migrations, models


def _default_antecedencias():
    return [1]


def preencher_antecedencia_padrao(apps, schema_editor):
    WhatsAppConfig = apps.get_model("whatsapp", "WhatsAppConfig")
    WhatsAppConfig.objects.filter(confirmacao_antecedencias_dias=[]).update(
        confirmacao_antecedencias_dias=[1],
    )


class Migration(migrations.Migration):

    dependencies = [
        ("whatsapp", "0007_mensagem_confirmacao_agenda"),
    ]

    operations = [
        migrations.AddField(
            model_name="whatsappconfig",
            name="confirmacao_antecedencias_dias",
            field=models.JSONField(
                blank=True,
                default=_default_antecedencias,
                help_text=(
                    "Lista de dias antes da consulta para enviar o link. "
                    "Ex.: [3, 1] envia 3 dias antes e de novo 1 dia antes. "
                    "O link não é enviado na criação do agendamento."
                ),
                verbose_name="Dias de antecedência do link de confirmação",
            ),
        ),
        migrations.CreateModel(
            name="WhatsAppConfirmacaoEnvio",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("appointment_id", models.PositiveIntegerField()),
                ("modulo", models.CharField(default="clinica_beleza", max_length=32)),
                ("regra_dias", models.PositiveSmallIntegerField()),
                ("enviado_em", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Envio de confirmação de agenda",
                "verbose_name_plural": "Envios de confirmação de agenda",
            },
        ),
        migrations.AddIndex(
            model_name="whatsappconfirmacaoenvio",
            index=models.Index(fields=["modulo", "appointment_id"], name="wa_conf_envio_appt_idx"),
        ),
        migrations.AddConstraint(
            model_name="whatsappconfirmacaoenvio",
            constraint=models.UniqueConstraint(
                fields=("modulo", "appointment_id", "regra_dias"),
                name="whatsapp_confirmacao_envio_unico",
            ),
        ),
        migrations.RunPython(preencher_antecedencia_padrao, migrations.RunPython.noop),
    ]
