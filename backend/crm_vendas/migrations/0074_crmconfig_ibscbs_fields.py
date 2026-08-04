"""Campos IBS/CBS (Reforma Tributária) para DPS Nacional v1.01."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm_vendas", "0073_crmconfig_issnet_nacional_fields"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="crmconfig",
                    name="indicador_operacao",
                    field=models.CharField(
                        blank=True,
                        default="",
                        help_text="Código do indicador da operação (cIndOp) do bloco IBS/CBS. Vazio: builder deriva pelo cTribNac.",
                        max_length=2,
                        verbose_name="Indicador da Operação (IBS/CBS)",
                    ),
                ),
                migrations.AddField(
                    model_name="crmconfig",
                    name="cst_ibscbs",
                    field=models.CharField(
                        blank=True,
                        default="",
                        help_text="Código de Situação Tributária de 3 dígitos do bloco IBS/CBS. Vazio: usa '000'.",
                        max_length=3,
                        verbose_name="Situação Tributária IBS/CBS (CST)",
                    ),
                ),
                migrations.AddField(
                    model_name="crmconfig",
                    name="cclass_trib_ibscbs",
                    field=models.CharField(
                        blank=True,
                        default="",
                        help_text="Código de Classificação Tributária de 6 dígitos do bloco IBS/CBS. Vazio: usa '000001'.",
                        max_length=6,
                        verbose_name="Classificação Tributária IBS/CBS (cClassTrib)",
                    ),
                ),
                migrations.AddField(
                    model_name="crmconfig",
                    name="p_tot_trib_sn",
                    field=models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=5,
                        null=True,
                        help_text="Percentual aproximado dos tributos (pTotTribSN), exigido para ME/EPP. Vazio: usa a alíquota de ISS.",
                        verbose_name="% Total de Tributos (Simples Nacional)",
                    ),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE crm_vendas_crmconfig "
                        "ADD COLUMN IF NOT EXISTS indicador_operacao varchar(2) NOT NULL DEFAULT '';"
                    ),
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE crm_vendas_crmconfig "
                        "ADD COLUMN IF NOT EXISTS cst_ibscbs varchar(3) NOT NULL DEFAULT '';"
                    ),
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE crm_vendas_crmconfig "
                        "ADD COLUMN IF NOT EXISTS cclass_trib_ibscbs varchar(6) NOT NULL DEFAULT '';"
                    ),
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE crm_vendas_crmconfig "
                        "ADD COLUMN IF NOT EXISTS p_tot_trib_sn numeric(5,2) NULL;"
                    ),
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
        ),
    ]
