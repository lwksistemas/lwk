# Generated manually for histórico de negociação CRM

import django.db.models.deletion
from django.db import migrations, models

import core.mixins


class Migration(migrations.Migration):

    dependencies = [
        ("crm_vendas", "0068_emitente_documento_snapshot"),
    ]

    operations = [
        migrations.AddField(
            model_name="oportunidade",
            name="feedback_pos_venda",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Opinião do cliente após fechamento ganho (sobre o serviço/sistema)",
            ),
        ),
        migrations.AddField(
            model_name="oportunidade",
            name="motivo_perda",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Motivo pelo qual a negociação foi perdida ou cancelada",
            ),
        ),
        migrations.CreateModel(
            name="OportunidadeNota",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True)),
                ("tipo", models.CharField(
                    choices=[("resposta_cliente", "Resposta do cliente"), ("nota_interna", "Nota interna")],
                    default="resposta_cliente",
                    max_length=30,
                )),
                ("texto", models.TextField()),
                ("autor_nome", models.CharField(blank=True, default="", max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("oportunidade", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="notas_negociacao",
                    to="crm_vendas.oportunidade",
                )),
            ],
            options={
                "verbose_name": "Nota de negociação",
                "verbose_name_plural": "Notas de negociação",
                "db_table": "crm_vendas_oportunidade_nota",
                "ordering": ["created_at"],
            },
            bases=(core.mixins.LojaIsolationMixin, models.Model),
        ),
        migrations.AddIndex(
            model_name="oportunidadenota",
            index=models.Index(fields=["loja_id", "oportunidade"], name="crm_opor_nota_loja_op_idx"),
        ),
        migrations.AddIndex(
            model_name="oportunidadenota",
            index=models.Index(fields=["loja_id", "created_at"], name="crm_opor_nota_loja_dt_idx"),
        ),
    ]
