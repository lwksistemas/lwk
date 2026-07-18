# Número sequencial da consulta por loja (001, 002, …).

from django.db import migrations, models


def backfill_numeros(apps, schema_editor):
    """Numera todas as consultas do schema (inclui loja_id NULL — bug da 0062 original)."""
    Consulta = apps.get_model("clinica_beleza", "Consulta")
    n = 1
    for consulta_id in Consulta.objects.order_by("id").values_list("id", flat=True):
        Consulta.objects.filter(pk=consulta_id).update(numero=n)
        n += 1


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0061_uniq_payment_per_appointment"),
    ]

    operations = [
        migrations.AddField(
            model_name="consulta",
            name="numero",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Número sequencial da consulta na loja (ex.: 1 → 001).",
                null=True,
                verbose_name="Número",
            ),
        ),
        migrations.RunPython(backfill_numeros, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="consulta",
            constraint=models.UniqueConstraint(
                fields=("loja_id", "numero"),
                name="uniq_consulta_numero_por_loja",
            ),
        ),
    ]
