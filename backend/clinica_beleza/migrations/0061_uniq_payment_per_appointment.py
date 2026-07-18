# Dedupe payments por appointment e garante 1 Payment por agendamento.

from django.db import migrations, models
from django.db.models import Count


def dedupe_payments(apps, schema_editor):
    Payment = apps.get_model("clinica_beleza", "Payment")
    PaymentParcela = apps.get_model("clinica_beleza", "PaymentParcela")

    dupes = (
        Payment.objects.values("appointment_id")
        .annotate(c=Count("id"))
        .filter(c__gt=1)
    )
    for row in dupes:
        appt_id = row["appointment_id"]
        payments = list(
            Payment.objects.filter(appointment_id=appt_id).order_by("-id"),
        )
        if len(payments) < 2:
            continue
        keep = payments[0]
        for payment in payments[1:]:
            PaymentParcela.objects.filter(payment_id=payment.id).update(payment_id=keep.id)
            payment.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0060_payment_desconto_parcela_index"),
    ]

    operations = [
        migrations.RunPython(dedupe_payments, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="payment",
            constraint=models.UniqueConstraint(
                fields=("appointment",),
                name="uniq_payment_per_appointment",
            ),
        ),
    ]
