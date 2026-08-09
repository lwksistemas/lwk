from django.db import migrations, models


class Migration(migrations.Migration):
    """Campos DPS/ADN na config NFS-e da clínica (paridade com CRMConfig)."""

    dependencies = [
        ("clinica_beleza", "0066_paciente_foto_rename_db_columns"),
    ]

    operations = [
        migrations.AddField(
            model_name="clinicabelezanfseconfig",
            name="issnet_usar_padrao_nacional",
            field=models.BooleanField(
                default=True,
                help_text="Se True, emite via webservice Nacional ISSNet (DPS/RTC).",
                verbose_name="Usar padrão Nacional (DPS/RTC)",
            ),
        ),
        migrations.AddField(
            model_name="clinicabelezanfseconfig",
            name="codigo_tributacao_nacional",
            field=models.CharField(
                blank=True,
                default="",
                max_length=10,
                verbose_name="Código de Tributação Nacional (cTribNac)",
            ),
        ),
        migrations.AddField(
            model_name="clinicabelezanfseconfig",
            name="codigo_tributacao_municipal",
            field=models.CharField(
                blank=True,
                default="",
                max_length=10,
                verbose_name="Código de Tributação Municipal (cTribMun)",
            ),
        ),
        migrations.AddField(
            model_name="clinicabelezanfseconfig",
            name="nacional_codigo_municipio",
            field=models.CharField(
                blank=True,
                default="",
                max_length=7,
                verbose_name="Código IBGE do município (API Nacional)",
            ),
        ),
        migrations.AddField(
            model_name="clinicabelezanfseconfig",
            name="indicador_operacao",
            field=models.CharField(
                blank=True,
                default="",
                max_length=2,
                verbose_name="Indicador da Operação (IBS/CBS)",
            ),
        ),
        migrations.AddField(
            model_name="clinicabelezanfseconfig",
            name="cst_ibscbs",
            field=models.CharField(
                blank=True,
                default="",
                max_length=3,
                verbose_name="Situação Tributária IBS/CBS (CST)",
            ),
        ),
        migrations.AddField(
            model_name="clinicabelezanfseconfig",
            name="cclass_trib_ibscbs",
            field=models.CharField(
                blank=True,
                default="",
                max_length=6,
                verbose_name="Classificação Tributária IBS/CBS (cClassTrib)",
            ),
        ),
        migrations.AddField(
            model_name="clinicabelezanfseconfig",
            name="p_tot_trib_sn",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=5,
                null=True,
                verbose_name="% Total de Tributos (Simples Nacional)",
            ),
        ),
        migrations.AlterField(
            model_name="clinicabelezanfseconfig",
            name="provedor_nf",
            field=models.CharField(
                choices=[
                    ("asaas", "Asaas (conta da sua loja)"),
                    ("issnet", "ISSNet — Padrão Nacional (DPS / RTC)"),
                    ("nacional", "API Nacional NFS-e (Direto)"),
                    ("manual", "Emissão Manual (Sem integração)"),
                ],
                default="asaas",
                help_text="Sistema usado para emitir notas fiscais de serviço",
                max_length=20,
                verbose_name="Provedor de Nota Fiscal",
            ),
        ),
    ]
