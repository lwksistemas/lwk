# Generated manually
# Adiciona campo conta (empresa) na Atividade para vincular interações a contas

from django.db import migrations, models
import django.db.models.deletion


def add_conta_column(apps, schema_editor):
    """Adiciona coluna conta_id se não existir (seguro para re-execução)."""
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute(
            "ALTER TABLE crm_vendas_atividade "
            "ADD COLUMN IF NOT EXISTS conta_id BIGINT NULL "
            "REFERENCES crm_vendas_conta(id) ON DELETE CASCADE;"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS crm_ativ_loja_conta_idx "
            "ON crm_vendas_atividade (loja_id, conta_id);"
        )


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0055_produtoservico_recorrencia'),
    ]

    operations = [
        migrations.RunPython(add_conta_column, migrations.RunPython.noop),
    ]
