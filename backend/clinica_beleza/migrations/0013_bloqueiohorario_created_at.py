# Migração manual: Adicionar created_at do BloqueioAgendaBase ao BloqueioHorario

from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_beleza', '0012_rename_patient_procedure_professional_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='bloqueiohorario',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True,
                verbose_name='Criado em',
                default=timezone.now,
            ),
            preserve_default=False,
        ),
    ]
