"""Alinha o estado das migrations com o modelo: loja_id (IntegerField) → loja (ForeignKey, db_column=loja_id).
A tabela já tem a coluna e a FK criadas em 0051_googlecalendar_loja_fk_cascade (RunSQL); não alterar a BD aqui.
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("superadmin", "0052_nfseemitida_loja_set_null"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveConstraint(
                    model_name="googlecalendarconnection",
                    name="gcal_loja_owner_uniq",
                ),
                migrations.RemoveConstraint(
                    model_name="googlecalendarconnection",
                    name="gcal_loja_vendedor_uniq",
                ),
                migrations.RemoveField(
                    model_name="googlecalendarconnection",
                    name="loja_id",
                ),
                migrations.AddField(
                    model_name="googlecalendarconnection",
                    name="loja",
                    field=models.ForeignKey(
                        db_column="loja_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="google_calendar_connections",
                        to="superadmin.loja",
                    ),
                ),
                migrations.AddConstraint(
                    model_name="googlecalendarconnection",
                    constraint=models.UniqueConstraint(
                        condition=models.Q(vendedor_id__isnull=True),
                        fields=("loja",),
                        name="gcal_loja_owner_uniq",
                    ),
                ),
                migrations.AddConstraint(
                    model_name="googlecalendarconnection",
                    constraint=models.UniqueConstraint(
                        condition=models.Q(vendedor_id__isnull=False),
                        fields=("loja", "vendedor_id"),
                        name="gcal_loja_vendedor_uniq",
                    ),
                ),
            ],
            database_operations=[],
        ),
    ]
