from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("superadmin", "0071_cora_config"),
    ]

    operations = [
        migrations.CreateModel(
            name="CredencialRosto",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("escopo", models.CharField(max_length=80)),
                ("credential_id", models.CharField(max_length=512, unique=True)),
                ("public_key", models.TextField()),
                ("sign_count", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_used_at", models.DateTimeField(blank=True, null=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="credenciais_rosto",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "superadmin_credencial_rosto",
                "indexes": [models.Index(fields=["user", "escopo"], name="rosto_user_escopo_idx")],
            },
        ),
    ]
