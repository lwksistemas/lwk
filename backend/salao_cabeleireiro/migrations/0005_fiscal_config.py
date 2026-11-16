from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("salao_cabeleireiro", "0004_recebimento_partes"),
    ]

    operations = [
        migrations.CreateModel(
            name="SalaoNFSeConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("provedor_nf", models.CharField(choices=[("asaas", "Asaas (conta da sua loja)"), ("issnet", "ISSNet — Padrão Nacional (DPS / RTC)"), ("nacional", "API Nacional NFS-e (Direto)"), ("manual", "Emissão Manual (Sem integração)")], default="asaas", help_text="Sistema usado para emitir notas fiscais de serviço", max_length=20, verbose_name="Provedor de Nota Fiscal")),
                ("issnet_usuario", models.CharField(blank=True, max_length=100, verbose_name="Usuário ISSNet")),
                ("issnet_senha", models.CharField(blank=True, max_length=500, verbose_name="Senha ISSNet")),
                ("issnet_certificado", models.BinaryField(blank=True, null=True, verbose_name="Certificado Digital A1 (.pfx)")),
                ("issnet_certificado_nome", models.CharField(blank=True, max_length=255, verbose_name="Nome do arquivo .pfx")),
                ("issnet_senha_certificado", models.CharField(blank=True, max_length=500, verbose_name="Senha do Certificado")),
                ("issnet_ambiente_homologacao", models.BooleanField(default=False, verbose_name="ISSNet homologação (teste)")),
                ("inscricao_municipal", models.CharField(blank=True, max_length=20, verbose_name="Inscrição Municipal")),
                ("codigo_cnae", models.CharField(blank=True, max_length=20, verbose_name="Código CNAE")),
                ("optante_simples_nacional", models.BooleanField(default=True, verbose_name="Optante pelo Simples Nacional")),
                ("regime_especial_tributacao", models.CharField(blank=True, default="0", max_length=2, verbose_name="Regime Especial de Tributação")),
                ("incentivador_cultural", models.BooleanField(default=False, verbose_name="Incentivador Cultural")),
                ("item_lista_servico", models.CharField(blank=True, max_length=10, verbose_name="Item da Lista de Serviços (LC 116)")),
                ("codigo_nbs", models.CharField(blank=True, max_length=20, verbose_name="Código NBS")),
                ("issnet_serie_rps", models.CharField(blank=True, default="", max_length=10, verbose_name="Série do RPS")),
                ("issnet_ultimo_rps_conhecido", models.IntegerField(default=0, verbose_name="Último RPS emitido")),
                ("issnet_numero_lote", models.IntegerField(default=0, verbose_name="Número do Lote")),
                ("codigo_servico_municipal", models.CharField(default="0602", max_length=10, verbose_name="Código do Serviço Municipal")),
                ("descricao_servico_padrao", models.TextField(default="Serviços de cabeleireiro", verbose_name="Descrição Padrão do Serviço")),
                ("aliquota_iss", models.DecimalField(decimal_places=2, default=2.0, max_digits=5, verbose_name="Alíquota ISS (%)")),
                ("emitir_nf_automaticamente", models.BooleanField(default=False, help_text="Desligado por padrão. O salão só emite a nota de serviço quando esta opção está ligada.", verbose_name="Emitir NF Automaticamente")),
                ("issnet_usar_padrao_nacional", models.BooleanField(default=True, help_text="Se True, emite via webservice Nacional ISSNet (DPS/RTC).", verbose_name="Usar padrão Nacional (DPS/RTC)")),
                ("codigo_tributacao_nacional", models.CharField(blank=True, default="", max_length=10, verbose_name="Código de Tributação Nacional (cTribNac)")),
                ("codigo_tributacao_municipal", models.CharField(blank=True, default="", max_length=10, verbose_name="Código de Tributação Municipal (cTribMun)")),
                ("nacional_codigo_municipio", models.CharField(blank=True, default="", max_length=7, verbose_name="Código IBGE do município (API Nacional)")),
                ("indicador_operacao", models.CharField(blank=True, default="", max_length=2, verbose_name="Indicador da Operação (IBS/CBS)")),
                ("cst_ibscbs", models.CharField(blank=True, default="", max_length=3, verbose_name="Situação Tributária IBS/CBS (CST)")),
                ("cclass_trib_ibscbs", models.CharField(blank=True, default="", max_length=6, verbose_name="Classificação Tributária IBS/CBS (cClassTrib)")),
                ("p_tot_trib_sn", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, verbose_name="% Total de Tributos (Simples Nacional)")),
                ("asaas_api_key", models.TextField(blank=True, default="", verbose_name="API Key Asaas (loja)")),
                ("asaas_sandbox", models.BooleanField(default=False, verbose_name="Asaas sandbox (homologação)")),
                ("asaas_webhook_token", models.TextField(blank=True, default="", verbose_name="Token webhook Asaas (loja)")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Configuração NFS-e (Salão)",
                "verbose_name_plural": "Configurações NFS-e (Salões)",
                "db_table": "salao_nfse_config",
            },
        ),
        migrations.CreateModel(
            name="SalaoNfceConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("habilitada", models.BooleanField(default=False, verbose_name="Emitir NFC-e nas vendas de produto")),
                ("regime", models.CharField(blank=True, choices=[("simples", "Simples Nacional"), ("normal", "Regime normal")], default="", max_length=12)),
                ("id_csc", models.CharField(blank=True, default="", max_length=6, verbose_name="ID do CSC")),
                ("csc", models.CharField(blank=True, default="", max_length=500)),
                ("inscricao_estadual", models.CharField(blank=True, default="", max_length=20)),
                ("serie", models.PositiveSmallIntegerField(default=1)),
                ("proximo_numero", models.PositiveIntegerField(default=1)),
                ("proximo_numero_teste", models.PositiveIntegerField(default=1)),
                ("ambiente_homologacao", models.BooleanField(default=True, verbose_name="Homologação")),
                ("ncm_padrao", models.CharField(blank=True, default="", max_length=8)),
                ("codigo_municipio", models.CharField(blank=True, default="", max_length=7)),
                ("aliquota_icms", models.DecimalField(decimal_places=2, default=18, max_digits=5)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Configuração NFC-e (Salão)",
                "db_table": "salao_nfce_config",
            },
        ),
        migrations.AddConstraint(
            model_name="salaonfseconfig",
            constraint=models.UniqueConstraint(fields=("loja_id",), name="salao_nfse_config_loja"),
        ),
        migrations.AddConstraint(
            model_name="salaonfceconfig",
            constraint=models.UniqueConstraint(fields=("loja_id",), name="salao_nfce_config_loja"),
        ),
    ]
