from django.db import migrations, models


def desligar_emissao_automatica(apps, schema_editor):
    ClinicaBelezaNFSeConfig = apps.get_model("clinica_beleza", "ClinicaBelezaNFSeConfig")
    ClinicaBelezaNFSeConfig.objects.filter(emitir_nf_automaticamente=True).update(
        emitir_nf_automaticamente=False,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0063_anamnese_tipo_pele_pressao_text"),
    ]

    operations = [
        migrations.AlterField(
            model_name="clinicabelezanfseconfig",
            name="emitir_nf_automaticamente",
            field=models.BooleanField(
                default=False,
                help_text="Desligado por padrão. Só emite NFS-e ao finalizar consulta se a clínica ativar.",
                verbose_name="Emitir NF Automaticamente",
            ),
        ),
        migrations.RunPython(desligar_emissao_automatica, migrations.RunPython.noop),
    ]
