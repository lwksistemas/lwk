# Termo de consentimento — assinatura separada por procedimento
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0037_termo_consentimento_assinatura"),
    ]

    operations = [
        migrations.CreateModel(
            name="ConsultaTermoProcedimento",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True)),
                ("conteudo_termo", models.TextField(blank=True, default="", verbose_name="Conteúdo do termo")),
                ("status_assinatura_termo", models.CharField(
                    choices=[
                        ("rascunho", "Rascunho"),
                        ("aguardando_paciente", "Aguardando Paciente"),
                        ("aguardando_profissional", "Aguardando Profissional"),
                        ("concluido", "Concluído"),
                    ],
                    default="rascunho",
                    max_length=30,
                    verbose_name="Status assinatura",
                )),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("consulta", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="termos_procedimentos",
                    to="clinica_beleza.consulta",
                )),
                ("procedure", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="termos_consulta",
                    to="clinica_beleza.procedure",
                )),
            ],
            options={
                "verbose_name": "Termo de procedimento",
                "verbose_name_plural": "Termos de procedimentos",
                "db_table": "clinica_beleza_consulta_termo_procedimento",
                "ordering": ["procedure__nome"],
            },
        ),
        migrations.AddConstraint(
            model_name="consultatermoprocedimento",
            constraint=models.UniqueConstraint(
                fields=("consulta", "procedure"),
                name="clin_cb_termo_cons_proc_uniq",
            ),
        ),
        migrations.AddIndex(
            model_name="consultatermoprocedimento",
            index=models.Index(fields=["consulta", "status_assinatura_termo"], name="clin_cb_termo_cons_st_idx"),
        ),
        migrations.AddField(
            model_name="consultaassinaturatermo",
            name="termo_procedimento",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="assinaturas",
                to="clinica_beleza.consultatermoprocedimento",
            ),
        ),
        migrations.AddIndex(
            model_name="consultaassinaturatermo",
            index=models.Index(fields=["termo_procedimento", "tipo"], name="clin_cb_assin_termo_tipo_idx"),
        ),
    ]
