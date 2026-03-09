# Adiciona duracao_minutos em schemas que têm crm_vendas_atividade.
# Usa RunPython para ser resiliente: tabela não existe no schema public (só em tenants).

from django.db import migrations, models


def add_duracao_minutos_if_table_exists(apps, schema_editor):
    """Adiciona coluna duracao_minutos apenas se a tabela crm_vendas_atividade existir."""
    conn = schema_editor.connection
    if conn.vendor != 'postgresql':
        return
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = COALESCE(current_schema(), 'public')
            AND table_name = 'crm_vendas_atividade'
        """)
        if not cursor.fetchone():
            return
        cursor.execute("""
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = COALESCE(current_schema(), 'public')
            AND table_name = 'crm_vendas_atividade'
            AND column_name = 'duracao_minutos'
        """)
        if cursor.fetchone():
            return
        cursor.execute("""
            ALTER TABLE crm_vendas_atividade
            ADD COLUMN duracao_minutos INTEGER NOT NULL DEFAULT 60
        """)


def reverse_add_duracao_minutos(apps, schema_editor):
    """No-op: não remove a coluna no reverse."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0004_ensure_google_event_id_in_tenant_schemas'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='atividade',
                    name='duracao_minutos',
                    field=models.PositiveIntegerField(default=60, help_text='Duração estimada da atividade em minutos'),
                ),
            ],
            database_operations=[
                migrations.RunPython(add_duracao_minutos_if_table_exists, reverse_add_duracao_minutos),
            ],
        ),
    ]
