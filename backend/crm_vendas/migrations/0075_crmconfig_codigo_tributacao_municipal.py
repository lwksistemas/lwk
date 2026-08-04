"""Campo cTribMun (Código de Tributação Municipal) dedicado para DPS Nacional."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm_vendas", "0074_crmconfig_ibscbs_fields"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="crmconfig",
                    name="codigo_tributacao_municipal",
                    field=models.CharField(
                        blank=True,
                        default="",
                        help_text=(
                            "Código de 6 dígitos cadastrado no ISSNet para este contribuinte/atividade "
                            "(NÃO é simplesmente o item da lista de serviço). Confirme junto à prefeitura "
                            "ou emitindo manualmente no portal ISSNet e inspecionando o XML gerado. "
                            "Vazio: usa o mesmo valor do cTribNac como fallback."
                        ),
                        max_length=10,
                        verbose_name="Código de Tributação Municipal (cTribMun)",
                    ),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE crm_vendas_config "
                        "ADD COLUMN IF NOT EXISTS codigo_tributacao_municipal varchar(10) NOT NULL DEFAULT '';"
                    ),
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
        ),
    ]
