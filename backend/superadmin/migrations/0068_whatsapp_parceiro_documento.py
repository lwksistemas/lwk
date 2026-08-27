from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("superadmin", "0067_whatsapp_gateway"),
    ]

    operations = [
        migrations.AlterField(
            model_name="whatsappapikey",
            name="prefixo",
            field=models.CharField(max_length=40),
        ),
        migrations.AlterField(
            model_name="whatsappcustomer",
            name="documento",
            field=models.CharField(blank=True, db_index=True, default="", max_length=18),
        ),
        migrations.AlterField(
            model_name="whatsappcustomer",
            name="quota_numeros",
            field=models.PositiveSmallIntegerField(default=50),
        ),
        migrations.AddConstraint(
            model_name="whatsappcustomer",
            constraint=models.UniqueConstraint(
                condition=models.Q(("tipo", "parceiro")) & ~models.Q(("documento", "")),
                fields=("documento",),
                name="uniq_whatsapp_parceiro_documento",
            ),
        ),
    ]
