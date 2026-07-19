from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0062_consulta_numero"),
    ]

    operations = [
        migrations.AlterField(
            model_name="patientanamnese",
            name="tipo_pele",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AlterField(
            model_name="patientanamnese",
            name="pressao_arterial",
            field=models.TextField(blank=True, default=""),
        ),
    ]
