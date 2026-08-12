from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("radiologia", "0002_pedido_dicom_media"),
    ]

    operations = [
        migrations.AddField(
            model_name="equipamento",
            name="codigo_vinculo",
            field=models.CharField(
                blank=True,
                db_index=True,
                default="",
                help_text="Código aleatório LWK para parear/enviar exames deste aparelho",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="equipamento",
            name="numero_serie",
            field=models.CharField(
                blank=True,
                db_index=True,
                default="",
                help_text="Serial do ultrassom — vincula aparelho à clínica (CPF/CNPJ da loja)",
                max_length=64,
            ),
        ),
        migrations.AddConstraint(
            model_name="equipamento",
            constraint=models.UniqueConstraint(
                condition=models.Q(("numero_serie", ""), _negated=True),
                fields=("loja_id", "numero_serie"),
                name="rad_equip_loja_serial_uniq",
            ),
        ),
    ]
