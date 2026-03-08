# Corrige coluna google_event_id em schemas de tenant (0002 usava connection padrão)
# Usa schema_editor.connection para rodar no schema correto

from django.db import migrations


def add_google_event_id_column(apps, schema_editor):
    """Adiciona google_event_id usando a conexão do schema_editor (tenant correto)."""
    conn = schema_editor.connection
    if conn.vendor != 'postgresql':
        return
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = current_schema()
            AND table_name = 'crm_vendas_atividade'
            AND column_name = 'google_event_id'
        """)
        if cursor.fetchone():
            return  # coluna já existe
        cursor.execute("""
            ALTER TABLE crm_vendas_atividade
            ADD COLUMN google_event_id VARCHAR(255) NULL
        """)


def reverse_add_google_event_id_column(apps, schema_editor):
    """Remove coluna google_event_id."""
    conn = schema_editor.connection
    if conn.vendor != 'postgresql':
        return
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = current_schema()
            AND table_name = 'crm_vendas_atividade'
            AND column_name = 'google_event_id'
        """)
        if cursor.fetchone():
            cursor.execute("ALTER TABLE crm_vendas_atividade DROP COLUMN google_event_id")


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0002_add_google_calendar_connection_and_google_event_id'),
    ]

    operations = [
        migrations.RunPython(add_google_event_id_column, reverse_add_google_event_id_column),
    ]
