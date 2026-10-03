from django.db import migrations


class Migration(migrations.Migration):
    """Remove o índice antigo de forma de pagamento. O nome do arquivo permanece pelo histórico."""

    dependencies = [
        ("superadmin", "0046_normalize_cpf_cnpj_add_index"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="loja",
            name="loja_forma_pag_idx",
        ),
    ]
