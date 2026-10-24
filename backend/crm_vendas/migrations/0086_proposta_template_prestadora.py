from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("crm_vendas", "0085_comissao_prestadora_regra"),
    ]

    operations = [
        migrations.AddField(
            model_name="propostatemplate",
            name="prestadora",
            field=models.ForeignKey(
                blank=True,
                help_text="Empresa prestadora. A proposta só lista os templates dessa prestadora.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="proposta_templates",
                to="crm_vendas.conta",
            ),
        ),
        migrations.AddIndex(
            model_name="propostatemplate",
            index=models.Index(fields=["loja_id", "prestadora"], name="crm_pt_loja_prest_idx"),
        ),
    ]
