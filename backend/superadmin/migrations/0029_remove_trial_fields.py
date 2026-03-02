# Generated manually on 2026-03-02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0028_add_storage_monitoring_fields'),
    ]

    operations = [
        # Remover índice que usa is_trial
        migrations.RemoveIndex(
            model_name='loja',
            name='loja_trial_idx',
        ),
        
        # Remover campos de trial
        migrations.RemoveField(
            model_name='loja',
            name='is_trial',
        ),
        migrations.RemoveField(
            model_name='loja',
            name='trial_ends_at',
        ),
    ]
