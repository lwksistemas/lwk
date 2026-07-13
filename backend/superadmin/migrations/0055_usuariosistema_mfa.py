from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("superadmin", "0054_nfseemitida_xml_dps_assinado_resposta_adn"),
    ]

    operations = [
        migrations.AddField(
            model_name="usuariosistema",
            name="mfa_enabled",
            field=models.BooleanField(
                default=False,
                help_text="Autenticação em duas etapas ativa",
            ),
        ),
        migrations.AddField(
            model_name="usuariosistema",
            name="mfa_totp_secret",
            field=models.TextField(
                blank=True,
                help_text="Secret TOTP criptografado (configurar via API MFA)",
            ),
        ),
    ]
