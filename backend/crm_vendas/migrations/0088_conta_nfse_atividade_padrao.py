from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm_vendas", "0087_nfse_descricao_template_prestadora"),
    ]

    operations = [
        migrations.AddField(
            model_name="conta",
            name="nfse_atividade_padrao",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Atividade municipal usada ao emitir a NFS-e desta prestadora.",
                max_length=20,
            ),
        ),
    ]
