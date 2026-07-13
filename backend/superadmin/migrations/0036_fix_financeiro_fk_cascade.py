# Generated manually on 2026-03-17 21:30
# Corrige constraint de foreign key em FinanceiroLoja para usar CASCADE (PostgreSQL).

from django.db import migrations


def fix_financeiro_fk_cascade(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute(
        """
        ALTER TABLE superadmin_financeiroloja
        DROP CONSTRAINT IF EXISTS superadmin_financeir_loja_id_5f812886_fk_superadmi;
        """,
    )
    schema_editor.execute(
        """
        ALTER TABLE superadmin_financeiroloja
        ADD CONSTRAINT superadmin_financeir_loja_id_5f812886_fk_superadmi
        FOREIGN KEY (loja_id)
        REFERENCES superadmin_loja(id)
        ON DELETE CASCADE
        DEFERRABLE INITIALLY DEFERRED;
        """,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("superadmin", "0035_googlecalendarconnection_vendedor"),
    ]

    operations = [
        migrations.RunPython(fix_financeiro_fk_cascade, migrations.RunPython.noop),
    ]
