# Generated manually

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("superadmin", "0047_cloudinaryconfig_remove_loja_loja_forma_pag_idx"),
    ]

    operations = [
        migrations.CreateModel(
            name="NFSeEmitida",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("numero_nf", models.CharField(blank=True, max_length=50, verbose_name="Número da NFS-e")),
                ("codigo_verificacao", models.CharField(blank=True, max_length=50, verbose_name="Código de Verificação")),
                ("numero_rps", models.IntegerField(default=0, verbose_name="Número do RPS")),
                ("serie_rps", models.CharField(blank=True, max_length=10, verbose_name="Série do RPS")),
                ("provedor", models.CharField(choices=[("issnet", "ISSNet (Direto)"), ("asaas", "Asaas (Intermediário)")], default="issnet", max_length=20)),
                ("status", models.CharField(choices=[("emitida", "Emitida"), ("cancelada", "Cancelada"), ("erro", "Erro"), ("pendente", "Pendente")], default="emitida", max_length=20)),
                ("valor", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("aliquota_iss", models.DecimalField(decimal_places=2, default=2.0, max_digits=5)),
                ("valor_iss", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("tomador_nome", models.CharField(blank=True, max_length=200)),
                ("tomador_cpf_cnpj", models.CharField(blank=True, max_length=18)),
                ("tomador_email", models.EmailField(blank=True, max_length=254)),
                ("descricao_servico", models.TextField(blank=True)),
                ("xml_nfse", models.TextField(blank=True, verbose_name="XML da NFS-e")),
                ("pdf_url", models.URLField(blank=True, verbose_name="URL do PDF")),
                ("asaas_invoice_id", models.CharField(blank=True, max_length=100)),
                ("asaas_payment_id", models.CharField(blank=True, max_length=100)),
                ("erro_mensagem", models.TextField(blank=True)),
                ("data_emissao", models.DateTimeField(blank=True, null=True)),
                ("data_cancelamento", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("loja", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="nfse_emitidas", to="superadmin.loja")),
                ("pagamento", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="nfse", to="superadmin.pagamentoloja")),
            ],
            options={
                "verbose_name": "NFS-e Emitida",
                "verbose_name_plural": "NFS-e Emitidas",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["loja", "-created_at"], name="nfse_loja_created_idx"),
                    models.Index(fields=["status", "-created_at"], name="nfse_status_created_idx"),
                    models.Index(fields=["asaas_payment_id"], name="nfse_asaas_pay_idx"),
                ],
            },
        ),
    ]
