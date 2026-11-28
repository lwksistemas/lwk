from django.db import migrations


def enable_completo(apps, schema_editor):
    Plano = apps.get_model("superadmin", "PlanoAssinatura")
    Plano.objects.filter(slug="profissional-clinica-beleza").update(
        tem_agendamento_online=True
    )


def disable_completo(apps, schema_editor):
    Plano = apps.get_model("superadmin", "PlanoAssinatura")
    Plano.objects.filter(slug="profissional-clinica-beleza").update(
        tem_agendamento_online=False
    )


class Migration(migrations.Migration):

    dependencies = [
        ("superadmin", "0080_plano_tem_agendamento_online"),
    ]

    operations = [
        migrations.RunPython(enable_completo, disable_completo),
    ]
