from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0068_termo_consentimento_template"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="procedure",
            constraint=models.UniqueConstraint(
                fields=("termo_template",),
                name="clin_cb_proc_termo_tpl_uniq",
            ),
        ),
    ]
