from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("superadmin", "0055_usuariosistema_mfa"),
    ]

    operations = [
        migrations.AddField(
            model_name="usuariosistema",
            name="mfa_backup_codes",
            field=models.TextField(
                blank=True,
                help_text="Hashes dos códigos de recuperação MFA (JSON criptografado)",
            ),
        ),
        migrations.CreateModel(
            name="LoginLockout",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("username_key", models.CharField(db_index=True, max_length=150, unique=True)),
                ("failed_attempts", models.PositiveSmallIntegerField(default=0)),
                ("locked_until", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Bloqueio de login",
                "verbose_name_plural": "Bloqueios de login",
            },
        ),
    ]
