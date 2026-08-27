from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("superadmin", "0066_maquina_radiologia_contrato_pacs"),
    ]

    operations = [
        migrations.CreateModel(
            name="WhatsappCustomer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tipo", models.CharField(choices=[("lwk_loja", "Loja LWK"), ("parceiro", "Parceiro (API)")], db_index=True, max_length=16)),
                ("nome", models.CharField(max_length=200)),
                ("documento", models.CharField(blank=True, default="", max_length=18)),
                ("quota_numeros", models.PositiveSmallIntegerField(default=1)),
                ("webhook_url", models.URLField(blank=True, default="", max_length=500)),
                ("is_active", models.BooleanField(default=True)),
                ("observacoes", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "loja",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="whatsapp_customer",
                        to="superadmin.loja",
                    ),
                ),
            ],
            options={
                "db_table": "superadmin_whatsapp_customer",
                "ordering": ["nome"],
            },
        ),
        migrations.CreateModel(
            name="WhatsappInstance",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("instance_name", models.CharField(max_length=80, unique=True)),
                ("rotulo", models.CharField(blank=True, default="", max_length=80)),
                ("telefone", models.CharField(blank=True, default="", max_length=32)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("connected", "Conectado"),
                            ("qr_pending", "Aguardando QR"),
                            ("disconnected", "Desconectado"),
                        ],
                        db_index=True,
                        default="disconnected",
                        max_length=20,
                    ),
                ),
                ("last_seen_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="instances",
                        to="superadmin.whatsappcustomer",
                    ),
                ),
            ],
            options={
                "db_table": "superadmin_whatsapp_instance",
                "ordering": ["customer_id", "id"],
            },
        ),
        migrations.CreateModel(
            name="WhatsappApiKey",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(default="padrão", max_length=80)),
                ("prefixo", models.CharField(max_length=24)),
                ("key_hash", models.CharField(max_length=64, unique=True)),
                ("last_used_at", models.DateTimeField(blank=True, null=True)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="api_keys",
                        to="superadmin.whatsappcustomer",
                    ),
                ),
            ],
            options={
                "db_table": "superadmin_whatsapp_api_key",
                "ordering": ["-id"],
            },
        ),
    ]
