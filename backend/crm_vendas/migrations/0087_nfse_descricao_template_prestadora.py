from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("crm_vendas", "0086_proposta_template_prestadora"),
    ]

    operations = [
        migrations.AddField(
            model_name="nfsedescricaotemplate",
            name="prestadora",
            field=models.ForeignKey(
                blank=True,
                help_text="Empresa prestadora. A nota dessa empresa usa este texto.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="nfse_descricao_templates",
                to="crm_vendas.conta",
            ),
        ),
        migrations.AddIndex(
            model_name="nfsedescricaotemplate",
            index=models.Index(fields=["loja_id", "prestadora"], name="crm_ndt_loja_prest_idx"),
        ),
    ]
