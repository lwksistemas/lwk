from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0072_payment_method_prazo"),
    ]

    operations = [
        migrations.AddField(
            model_name="patient",
            name="sexo",
            field=models.CharField(
                blank=True,
                choices=[("M", "Masculino"), ("F", "Feminino")],
                default="",
                help_text="Usado na identificação do paciente na prescrição digital (Memed).",
                max_length=1,
                verbose_name="Sexo",
            ),
        ),
    ]
