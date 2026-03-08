# Garante que google_event_id existe em schemas de tenant (corrige 0002 que usava connection padrão)

from django.db import migrations


def ensure_google_event_id(apps, schema_editor):
    """Adiciona google_event_id se a tabela existir e a coluna não existir."""
    conn = schema_editor.connection
    if conn.vendor != 'postgresql':
        return
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = current_schema()
            AND table_name = 'crm_vendas_atividade'
        """)
        if not cursor.fetchone():
            return
        cursor.execute("""
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = current_schema()
            AND table_name = 'crm_vendas_atividade'
            AND column_name = 'google_event_id'
        """)
        if cursor.fetchone():
            return
        cursor.execute("""
            ALTER TABLE crm_vendas_atividade
            ADD COLUMN google_event_id VARCHAR(255) NULL
        """)


def reverse_ensure_google_event_id(apps, schema_editor):
    """No-op: não remove a coluna no reverse."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0003_add_google_event_id_tenant_schemas'),
    ]

    operations = [
        migrations.RunPython(ensure_google_event_id, reverse_ensure_google_event_id),
    ]
