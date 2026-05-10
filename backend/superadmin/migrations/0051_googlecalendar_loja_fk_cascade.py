"""
Converte GoogleCalendarConnection.loja_id de IntegerField para ForeignKey(CASCADE).
Usa RunSQL para adicionar a FK constraint sem alterar a coluna existente.
Também limpa registros órfãos antes de adicionar a FK.
"""
from django.db import migrations, models
import django.db.models.deletion


def limpar_orfaos(apps, schema_editor):
    """Remove GoogleCalendarConnection com loja_id que não existe em superadmin_loja."""
    GoogleCalendarConnection = apps.get_model('superadmin', 'GoogleCalendarConnection')
    Loja = apps.get_model('superadmin', 'Loja')
    loja_ids = set(Loja.objects.values_list('id', flat=True))
    deleted, _ = GoogleCalendarConnection.objects.exclude(loja_id__in=loja_ids).delete()
    if deleted:
        print(f'\n   🗑️ Removidos {deleted} GoogleCalendarConnection órfãos')


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0050_auditlog'),
    ]

    operations = [
        # 1. Limpar órfãos
        migrations.RunPython(limpar_orfaos, migrations.RunPython.noop),

        # 2. Remover constraints antigas
        migrations.RunSQL(
            sql="ALTER TABLE superadmin_google_calendar_connection DROP CONSTRAINT IF EXISTS gcal_loja_owner_uniq;",
            reverse_sql="SELECT 1;",
        ),
        migrations.RunSQL(
            sql="ALTER TABLE superadmin_google_calendar_connection DROP CONSTRAINT IF EXISTS gcal_loja_vendedor_uniq;",
            reverse_sql="SELECT 1;",
        ),

        # 3. Adicionar FK constraint no PostgreSQL (coluna loja_id já existe)
        migrations.RunSQL(
            sql="""
                ALTER TABLE superadmin_google_calendar_connection
                ADD CONSTRAINT gcal_loja_fk
                FOREIGN KEY (loja_id) REFERENCES superadmin_loja(id)
                ON DELETE CASCADE;
            """,
            reverse_sql="ALTER TABLE superadmin_google_calendar_connection DROP CONSTRAINT IF EXISTS gcal_loja_fk;",
        ),

        # 4. Recriar unique constraints
        migrations.RunSQL(
            sql="""
                CREATE UNIQUE INDEX IF NOT EXISTS gcal_loja_owner_uniq
                ON superadmin_google_calendar_connection (loja_id)
                WHERE vendedor_id IS NULL;
            """,
            reverse_sql="DROP INDEX IF EXISTS gcal_loja_owner_uniq;",
        ),
        migrations.RunSQL(
            sql="""
                CREATE UNIQUE INDEX IF NOT EXISTS gcal_loja_vendedor_uniq
                ON superadmin_google_calendar_connection (loja_id, vendedor_id)
                WHERE vendedor_id IS NOT NULL;
            """,
            reverse_sql="DROP INDEX IF EXISTS gcal_loja_vendedor_uniq;",
        ),
    ]
