# Generated manually for NfseDescricaoTemplate

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm_vendas", "0075_crmconfig_codigo_tributacao_municipal"),
    ]

    operations = [
        migrations.CreateModel(
            name="NfseDescricaoTemplate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja (tenant)")),
                (
                    "nome",
                    models.CharField(
                        help_text="Nome do template (ex: Consultoria mensal, Treinamento)",
                        max_length=255,
                    ),
                ),
                ("conteudo", models.TextField(help_text="Texto da discriminação/descrição do serviço")),
                (
                    "is_padrao",
                    models.BooleanField(
                        default=False,
                        help_text="Template padrão usado ao emitir novas NFS-e",
                    ),
                ),
                ("ativo", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Template de Descrição NFS-e",
                "verbose_name_plural": "Templates de Descrição NFS-e",
                "db_table": "crm_vendas_nfse_descricao_template",
                "ordering": ["-is_padrao", "nome"],
                "indexes": [
                    models.Index(fields=["loja_id", "ativo"], name="crm_ndt_loja_ativo_idx"),
                    models.Index(fields=["loja_id", "is_padrao"], name="crm_ndt_loja_padrao_idx"),
                ],
            },
        ),
    ]
