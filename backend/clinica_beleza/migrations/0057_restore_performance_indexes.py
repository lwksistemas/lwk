"""Restaura índices de performance removidos acidentalmente na 0055."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0056_consulta_status_receber"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="consultaevolucao",
            index=models.Index(fields=["consulta", "-created_at"], name="cb_evolucao_consulta_idx"),
        ),
        migrations.AddIndex(
            model_name="documentoclinico",
            index=models.Index(fields=["consulta", "-created_at"], name="cb_documento_consulta_idx"),
        ),
        migrations.AddIndex(
            model_name="movimentacaoestoque",
            index=models.Index(fields=["produto", "-created_at"], name="cb_movest_produto_idx"),
        ),
        migrations.AddIndex(
            model_name="prescricaomemed",
            index=models.Index(fields=["patient", "-created_at"], name="cb_prescricao_patient_idx"),
        ),
        migrations.AddIndex(
            model_name="produtoestoque",
            index=models.Index(fields=["validade"], name="cb_estoque_validade_idx"),
        ),
    ]
