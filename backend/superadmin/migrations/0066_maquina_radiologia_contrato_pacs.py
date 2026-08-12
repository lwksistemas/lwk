from decimal import Decimal

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("superadmin", "0065_planoassinatura_tem_fotos_tem_memed"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContratoPacsLoja",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("dicom_contratado", models.BooleanField(default=False)),
                ("worklist_contratado", models.BooleanField(default=False)),
                ("cobranca_dicom_mensal", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10)),
                ("cobranca_worklist_mensal", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "loja",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="contrato_pacs",
                        to="superadmin.loja",
                    ),
                ),
            ],
            options={
                "verbose_name": "Contrato PACS da loja",
                "verbose_name_plural": "Contratos PACS",
                "db_table": "superadmin_contrato_pacs_loja",
            },
        ),
        migrations.CreateModel(
            name="MaquinaRadiologia",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("US", "Ultrassom"),
                            ("DX", "Raio-X"),
                            ("MG", "Mamógrafo"),
                            ("CR", "CR / Digitalizador"),
                            ("CT", "Tomógrafo"),
                            ("MR", "Ressonância"),
                        ],
                        default="US",
                        max_length=8,
                    ),
                ),
                ("nome", models.CharField(max_length=120)),
                ("ae_title", models.CharField(max_length=16)),
                ("fabricante", models.CharField(blank=True, default="", max_length=80)),
                ("modelo", models.CharField(blank=True, default="", max_length=80)),
                ("cobranca_mensal", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("cadastrada", "Cadastrada"),
                            ("liberada", "Liberada no cliente"),
                            ("suspensa", "Suspensa"),
                        ],
                        db_index=True,
                        default="cadastrada",
                        max_length=16,
                    ),
                ),
                ("codigo_vinculo", models.CharField(blank=True, default="", max_length=16)),
                ("equipamento_tenant_id", models.IntegerField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("observacoes", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("liberada_em", models.DateTimeField(blank=True, null=True)),
                (
                    "loja",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="maquinas_radiologia",
                        to="superadmin.loja",
                    ),
                ),
            ],
            options={
                "db_table": "superadmin_maquina_radiologia",
                "ordering": ["-id"],
            },
        ),
        migrations.AddConstraint(
            model_name="maquinaradiologia",
            constraint=models.UniqueConstraint(fields=("loja", "ae_title"), name="sa_maq_loja_aet_uniq"),
        ),
        migrations.AddIndex(
            model_name="maquinaradiologia",
            index=models.Index(fields=["loja", "status"], name="sa_maq_loja_status_idx"),
        ),
    ]
