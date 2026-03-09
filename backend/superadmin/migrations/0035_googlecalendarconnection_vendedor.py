# Migration: Google Calendar por vendedor (cada vendedor sincroniza sua própria conta)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0034_vendedor_usuario'),
    ]

    operations = [
        migrations.AlterField(
            model_name='googlecalendarconnection',
            name='loja_id',
            field=models.IntegerField(db_index=True),
        ),
        migrations.AddField(
            model_name='googlecalendarconnection',
            name='vendedor_id',
            field=models.IntegerField(blank=True, null=True, db_index=True),
        ),
        migrations.AddConstraint(
            model_name='googlecalendarconnection',
            constraint=models.UniqueConstraint(
                condition=models.Q(vendedor_id__isnull=True),
                fields=('loja_id',),
                name='gcal_loja_owner_uniq',
            ),
        ),
        migrations.AddConstraint(
            model_name='googlecalendarconnection',
            constraint=models.UniqueConstraint(
                condition=models.Q(vendedor_id__isnull=False),
                fields=('loja_id', 'vendedor_id'),
                name='gcal_loja_vendedor_uniq',
            ),
        ),
    ]
