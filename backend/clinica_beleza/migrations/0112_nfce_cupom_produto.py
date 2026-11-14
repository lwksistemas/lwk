from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0111_termo_logo_assinatura"),
    ]

    operations = [
        migrations.AddField(
            model_name="produtoestoque",
            name="ncm",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Oito dígitos do cupom fiscal. Vazio usa o NCM padrão da clínica, se houver.",
                max_length=8,
                verbose_name="NCM",
            ),
        ),
        migrations.CreateModel(
            name="NfceConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("habilitada", models.BooleanField(default=False, verbose_name="Emitir NFC-e nas vendas de produto")),
                ("regime", models.CharField(blank=True, default="", max_length=12)),
                ("id_csc", models.CharField(blank=True, default="", max_length=6, verbose_name="ID do CSC")),
                ("csc", models.CharField(blank=True, default="", max_length=500, verbose_name="CSC")),
                ("inscricao_estadual", models.CharField(blank=True, default="", max_length=20)),
                ("serie", models.PositiveSmallIntegerField(default=1)),
                ("proximo_numero", models.PositiveIntegerField(default=1)),
                ("proximo_numero_teste", models.PositiveIntegerField(default=1)),
                ("ambiente_homologacao", models.BooleanField(default=True, help_text="Ligado envia cupom de teste. Desligado envia NFC-e com valor fiscal.", verbose_name="Homologação")),
                ("ncm_padrao", models.CharField(blank=True, default="", max_length=8)),
                ("codigo_municipio", models.CharField(blank=True, default="", max_length=7, verbose_name="Código IBGE")),
                ("aliquota_icms", models.DecimalField(decimal_places=2, default=18, max_digits=5)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "Configuração de NFC-e"},
        ),
        migrations.CreateModel(
            name="NfceCupom",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("status", models.CharField(choices=[("pendente", "Pendente"), ("autorizada", "Autorizada"), ("rejeitada", "Rejeitada"), ("cancelada", "Cancelada")], default="pendente", max_length=12)),
                ("numero", models.PositiveIntegerField()),
                ("serie", models.PositiveSmallIntegerField(default=1)),
                ("homologacao", models.BooleanField(default=True)),
                ("chave", models.CharField(blank=True, default="", max_length=44)),
                ("protocolo", models.CharField(blank=True, default="", max_length=20)),
                ("qrcode", models.TextField(blank=True, default="")),
                ("xml", models.TextField(blank=True, default="")),
                ("motivo", models.TextField(blank=True, default="")),
                ("emitida_em", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("venda", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="cupom_nfce", to="clinica_beleza.vendabalcao")),
            ],
            options={"verbose_name": "Cupom fiscal"},
        ),
        migrations.AddConstraint(
            model_name="nfceconfig",
            constraint=models.UniqueConstraint(fields=("loja_id",), name="cb_nfce_config_loja"),
        ),
        migrations.AddConstraint(
            model_name="nfcecupom",
            constraint=models.UniqueConstraint(fields=("loja_id", "serie", "numero", "homologacao"), name="cb_nfce_cupom_numero"),
        ),
    ]
