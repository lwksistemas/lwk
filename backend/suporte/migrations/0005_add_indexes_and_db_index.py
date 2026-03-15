# Migration: índices para performance (loja_slug, usuario_email, status+created_at, etc.)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('suporte', '0004_errofrontend'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='chamado',
            index=models.Index(fields=['status', '-created_at'], name='chamado_status_created_idx'),
        ),
        migrations.AddIndex(
            model_name='errofrontend',
            index=models.Index(fields=['loja_slug', '-created_at'], name='errofrontend_loja_created_idx'),
        ),
        migrations.AlterField(
            model_name='chamado',
            name='loja_slug',
            field=models.CharField(db_index=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='chamado',
            name='usuario_email',
            field=models.EmailField(db_index=True, max_length=254),
        ),
    ]
