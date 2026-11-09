from django.db import migrations, models


def marcar_completo(apps, schema_editor):
    Plano = apps.get_model("superadmin", "PlanoAssinatura")
    Plano.objects.filter(slug="profissional-clinica-beleza").update(tem_simulacao_estetica=True)


def desmarcar_completo(apps, schema_editor):
    Plano = apps.get_model("superadmin", "PlanoAssinatura")
    Plano.objects.filter(slug="profissional-clinica-beleza").update(tem_simulacao_estetica=False)


class Migration(migrations.Migration):

    dependencies = [
        ("superadmin", "0077_loja_recibo_logo_cor"),
    ]

    operations = [
        migrations.AddField(
            model_name="planoassinatura",
            name="tem_simulacao_estetica",
            field=models.BooleanField(
                default=False,
                help_text="Permite a clínica configurar a própria chave de simulação estética.",
            ),
        ),
        migrations.RunPython(marcar_completo, desmarcar_completo),
    ]
