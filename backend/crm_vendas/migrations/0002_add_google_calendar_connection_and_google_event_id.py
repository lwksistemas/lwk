# Generated manually for Google Calendar sync (google_event_id only; GoogleCalendarConnection is in superadmin)
# Usa RunPython para ser resiliente em schemas onde a tabela pode não existir (multi-tenant)

from django.db import migrations, models


def add_google_event_id_if_table_exists(apps, schema_editor):
    """Adiciona coluna google_event_id apenas se a tabela crm_vendas_atividade existir."""
    conn = schema_editor.connection
    vendor = conn.vendor
    with conn.cursor() as cursor:
        if vendor == 'postgresql':
            cursor.execute("""
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'crm_vendas_atividade'
                AND table_schema = COALESCE(current_schema(), 'public')
            """)
            if cursor.fetchone():
                cursor.execute("""
                    ALTER TABLE crm_vendas_atividade
                    ADD COLUMN IF NOT EXISTS google_event_id VARCHAR(255) NULL
                """)
        elif vendor == 'sqlite':
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='crm_vendas_atividade'"
            )
            if cursor.fetchone():
                try:
                    cursor.execute(
                        "ALTER TABLE crm_vendas_atividade ADD COLUMN google_event_id VARCHAR(255) NULL"
                    )
                except Exception:
                    pass  # coluna já existe


def reverse_add_google_event_id(apps, schema_editor):
    """Remove coluna google_event_id se a tabela existir (apenas PostgreSQL suporta DROP COLUMN)."""
    conn = schema_editor.connection
    if conn.vendor != 'postgresql':
        return
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'crm_vendas_atividade'
            AND column_name = 'google_event_id'
            AND table_schema = COALESCE(current_schema(), 'public')
        """)
        if cursor.fetchone():
            cursor.execute("ALTER TABLE crm_vendas_atividade DROP COLUMN IF EXISTS google_event_id")


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='atividade',
                    name='google_event_id',
                    field=models.CharField(blank=True, help_text='ID do evento no Google Calendar (sincronização)', max_length=255, null=True),
                ),
            ],
            database_operations=[
                migrations.RunPython(add_google_event_id_if_table_exists, reverse_add_google_event_id),
            ],
        ),
    ]
