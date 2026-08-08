from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("superadmin", "0063_loja_telefone_email_contato"),
    ]

    operations = [
        migrations.DeleteModel(
            name="CloudinaryConfig",
        ),
    ]
