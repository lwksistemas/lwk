from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0021_appointment_duracao_minutos"),
    ]

    operations = [
        migrations.AddField(
            model_name="professional",
            name="conselho",
            field=models.CharField(
                blank=True, null=True, max_length=10,
                choices=[
                    ("CRM", "CRM - Medicina"),
                    ("CRO", "CRO - Odontologia"),
                    ("COREN", "COREN - Enfermagem"),
                    ("CRF", "CRF - Farmácia"),
                    ("CRP", "CRP - Psicologia"),
                    ("CRN", "CRN - Nutrição"),
                    ("CREFITO", "CREFITO - Fisioterapia/TO"),
                    ("CRBM", "CRBM - Biomedicina"),
                    ("CRMV", "CRMV - Veterinária"),
                    ("CRFa", "CRFa - Fonoaudiologia"),
                ],
                verbose_name="Conselho",
                help_text="Conselho de classe (CRM, COREN, CRF, etc.)",
            ),
        ),
        migrations.AddField(
            model_name="professional",
            name="conselho_uf",
            field=models.CharField(blank=True, null=True, max_length=2, verbose_name="UF do conselho"),
        ),
        migrations.AddField(
            model_name="professional",
            name="cpf",
            field=models.CharField(
                blank=True, null=True, max_length=14, verbose_name="CPF",
                help_text="CPF do prescritor (usado para assinar na Memed).",
            ),
        ),
    ]
