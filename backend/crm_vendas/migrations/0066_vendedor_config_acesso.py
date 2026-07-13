from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm_vendas", "0065_financeiro_recorrencia"),
    ]

    operations = [
        migrations.AddField(
            model_name="vendedor",
            name="config_acesso",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="Configuração de grupo/permissões (grupo_id, permissoes_ids) para acesso ao CRM",
            ),
        ),
    ]
