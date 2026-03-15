# Adiciona criado_por_vendedor_id para isolar atividades órfãs por vendedor (calendário Google)
# Cada vendedor vê apenas suas próprias tarefas; admin vê todas.

from django.db import migrations, models


def add_criado_por_vendedor_id_if_exists(apps, schema_editor):
    """Adiciona coluna criado_por_vendedor_id em crm_vendas_atividade se a tabela existir."""
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
            AND column_name = 'criado_por_vendedor_id'
        """)
        if cursor.fetchone():
            return
        cursor.execute("""
            ALTER TABLE crm_vendas_atividade
            ADD COLUMN criado_por_vendedor_id INTEGER NULL
        """)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0013_add_endereco_to_lead'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='atividade',
                    name='criado_por_vendedor_id',
                    field=models.PositiveIntegerField(
                        blank=True,
                        db_index=True,
                        help_text='Vendedor que criou/importou esta atividade (órfã). Null = proprietário.',
                        null=True,
                    ),
                ),
            ],
            database_operations=[
                migrations.RunPython(add_criado_por_vendedor_id_if_exists, noop_reverse),
            ],
        ),
    ]
