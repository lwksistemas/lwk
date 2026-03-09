# Adiciona vendedor em Lead e Conta - apenas em schemas onde as tabelas existem (tenants).
# No schema public as tabelas não existem; migrate_all_lojas aplica nos schemas das lojas.

from django.db import migrations, models
import django.db.models.deletion


def add_vendedor_columns_if_tables_exist(apps, schema_editor):
    """Adiciona coluna vendedor_id em lead e conta apenas se as tabelas existirem no schema atual."""
    conn = schema_editor.connection
    if conn.vendor != 'postgresql':
        return
    with conn.cursor() as cursor:
        # Lead
        cursor.execute("""
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = current_schema()
            AND table_name = 'crm_vendas_lead'
        """)
        if cursor.fetchone():
            cursor.execute("""
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = current_schema()
                AND table_name = 'crm_vendas_lead'
                AND column_name = 'vendedor_id'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    ALTER TABLE crm_vendas_lead
                    ADD COLUMN vendedor_id INTEGER NULL
                    REFERENCES crm_vendas_vendedor(id) ON DELETE SET NULL
                """)

        # Conta
        cursor.execute("""
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = current_schema()
            AND table_name = 'crm_vendas_conta'
        """)
        if cursor.fetchone():
            cursor.execute("""
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = current_schema()
                AND table_name = 'crm_vendas_conta'
                AND column_name = 'vendedor_id'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    ALTER TABLE crm_vendas_conta
                    ADD COLUMN vendedor_id INTEGER NULL
                    REFERENCES crm_vendas_vendedor(id) ON DELETE SET NULL
                """)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0005_add_duracao_minutos'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='lead',
                    name='vendedor',
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='leads',
                        to='crm_vendas.vendedor',
                        help_text='Vendedor responsável pelo lead (quando criado por vendedor)',
                    ),
                ),
                migrations.AddField(
                    model_name='conta',
                    name='vendedor',
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='contas',
                        to='crm_vendas.vendedor',
                        help_text='Vendedor responsável pela conta (quando criado por vendedor)',
                    ),
                ),
            ],
            database_operations=[
                migrations.RunPython(add_vendedor_columns_if_tables_exist, noop_reverse),
            ],
        ),
    ]
