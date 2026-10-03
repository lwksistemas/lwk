from django.db import migrations


class Migration(migrations.Migration):
    """Histórico já aplicado. A tabela legada não é mais criada."""

    dependencies = [
        ("superadmin", "0063_loja_telefone_email_contato"),
    ]

    operations = []
