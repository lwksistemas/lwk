from django.db import migrations


def _noop(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    """Histórico já aplicado. Não cria mais tabela de provedor externo de imagem."""

    dependencies = [
        ("superadmin", "0036_fix_financeiro_fk_cascade"),
    ]

    operations = [
        migrations.RunPython(_noop, migrations.RunPython.noop),
    ]
