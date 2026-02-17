# Patient.phone opcional (evita 400 ao cadastrar sem telefone)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_beleza', '0006_patient_allow_whatsapp'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patient',
            name='phone',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Telefone'),
        ),
    ]
