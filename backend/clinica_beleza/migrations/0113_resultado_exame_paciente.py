"""Tabela de resultado de exame (PDF do laboratório na consulta)."""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0112_nfce_cupom_produto"),
    ]

    operations = [
        migrations.CreateModel(
            name="ResultadoExamePaciente",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, verbose_name="ID da Loja")),
                ("pdf_url", models.URLField(blank=True, default="", max_length=500)),
                ("nome_arquivo", models.CharField(blank=True, default="", max_length=255)),
                ("texto_extraido", models.TextField(blank=True, default="")),
                ("marcadores", models.JSONField(blank=True, default=list, help_text="Lista de biomarcadores com valor, faixa e status da sugestão.")),
                ("sugestao_texto", models.TextField(blank=True, default="", help_text="Texto de apoio gerado pelas faixas de referência (não é diagnóstico).")),
                ("aviso_cadastro", models.CharField(blank=True, default="", help_text="Aviso quando falta sexo ou data de nascimento no cadastro.", max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("consulta", models.ForeignKey(help_text="Consulta em que o profissional importou o PDF.", on_delete=django.db.models.deletion.CASCADE, related_name="resultados_exame", to="clinica_beleza.consulta", verbose_name="Consulta do retorno")),
                ("consulta_origem", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="resultados_exame_origem", to="clinica_beleza.consulta", verbose_name="Consulta do pedido")),
                ("documento_origem", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="resultados_exame", to="clinica_beleza.documentoclinico", verbose_name="Pedido de exame (documento)")),
                ("patient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="resultados_exame", to="clinica_beleza.patient", verbose_name="Paciente")),
                ("prescricao_origem", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="resultados_exame", to="clinica_beleza.prescricaomemed", verbose_name="Pedido de exame (Memed)")),
            ],
            options={
                "verbose_name": "Resultado de exame",
                "verbose_name_plural": "Resultados de exame",
                "db_table": "clinica_beleza_resultado_exame",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="resultadoexamepaciente",
            index=models.Index(fields=["patient", "created_at"], name="cb_res_exame_pac_dt_idx"),
        ),
        migrations.AddIndex(
            model_name="resultadoexamepaciente",
            index=models.Index(fields=["consulta"], name="cb_res_exame_cons_idx"),
        ),
    ]
