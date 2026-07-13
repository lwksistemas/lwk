import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0022_professional_conselho_cpf"),
    ]

    operations = [
        migrations.CreateModel(
            name="PrescricaoMemed",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("prescricao_id", models.CharField(blank=True, default="", help_text="Identificador da prescrição retornado pela Memed.", max_length=64, verbose_name="ID na Memed")),
                ("resumo", models.TextField(blank=True, default="", help_text="Lista legível dos itens prescritos (medicamentos/exames).", verbose_name="Resumo")),
                ("itens", models.JSONField(blank=True, default=list, help_text="Itens estruturados da prescrição (nome, posologia, tipo, receituário).", verbose_name="Itens")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("consulta", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="prescricoes_memed", to="clinica_beleza.consulta", verbose_name="Consulta")),
                ("patient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="prescricoes_memed", to="clinica_beleza.patient", verbose_name="Cliente")),
                ("professional", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="clinica_beleza.professional", verbose_name="Profissional")),
            ],
            options={
                "verbose_name": "Prescrição Memed",
                "verbose_name_plural": "Prescrições Memed",
                "db_table": "clinica_beleza_prescricoes_memed",
                "ordering": ["-created_at"],
                "app_label": "clinica_beleza",
            },
        ),
    ]
