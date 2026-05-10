"""
Converte GoogleCalendarConnection.loja_id de IntegerField para ForeignKey(CASCADE).
A coluna no banco já existe (loja_id) — apenas adiciona a constraint FK.
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
        # 1. Limpar órfãos antes de adicionar FK constraint
        migrations.RunPython(limpar_orfaos, migrations.RunPython.noop),

        # 2. Remover constraints antigas (usam loja_id como field name)
        migrations.RemoveConstraint(
            model_name='googlecalendarconnection',
            name='gcal_loja_owner_uniq',
        ),
        migrations.RemoveConstraint(
            model_name='googlecalendarconnection',
            name='gcal_loja_vendedor_uniq',
        ),

        # 3. Alterar campo de IntegerField para ForeignKey
        migrations.AlterField(
            model_name='googlecalendarconnection',
            name='loja',
            field=models.ForeignKey(
                db_column='loja_id',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='google_calendar_connections',
                to='superadmin.loja',
            ),
        ),

        # 4. Recriar constraints com o novo field name
        migrations.AddConstraint(
            model_name='googlecalendarconnection',
            constraint=models.UniqueConstraint(
                condition=models.Q(vendedor_id__isnull=True),
                fields=['loja'],
                name='gcal_loja_owner_uniq',
            ),
        ),
        migrations.AddConstraint(
            model_name='googlecalendarconnection',
            constraint=models.UniqueConstraint(
                condition=models.Q(vendedor_id__isnull=False),
                fields=['loja', 'vendedor_id'],
                name='gcal_loja_vendedor_uniq',
            ),
        ),
    ]
