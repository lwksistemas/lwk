from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm_vendas", "0082_conta_logo"),
    ]

    operations = [
        migrations.AddField(
            model_name="produtoservico",
            name="prestadora",
            field=models.ForeignKey(
                blank=True,
                help_text="Prestadora dona deste item. A oportunidade lista só o catálogo desta empresa.",
                null=True,
                on_delete=models.CASCADE,
                related_name="produtos_servicos",
                to="crm_vendas.conta",
            ),
        ),
        migrations.AddIndex(
            model_name="produtoservico",
            index=models.Index(fields=["loja_id", "prestadora"], name="crm_ps_loja_prest_idx"),
        ),
        migrations.RemoveConstraint(
            model_name="produtoservico",
            name="crm_ps_unique_codigo_loja",
        ),
        migrations.AddConstraint(
            model_name="produtoservico",
            constraint=models.UniqueConstraint(
                condition=models.Q(prestadora__isnull=True)
                & models.Q(codigo__isnull=False)
                & ~models.Q(codigo=""),
                fields=("loja_id", "codigo"),
                name="crm_ps_unique_codigo_sem_prestadora",
            ),
        ),
        migrations.AddConstraint(
            model_name="produtoservico",
            constraint=models.UniqueConstraint(
                condition=models.Q(prestadora__isnull=False)
                & models.Q(codigo__isnull=False)
                & ~models.Q(codigo=""),
                fields=("loja_id", "prestadora", "codigo"),
                name="crm_ps_unique_codigo_prestadora",
            ),
        ),
    ]
