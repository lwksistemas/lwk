# Generated migration for UserSession model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('superadmin', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_id', models.CharField(db_index=True, max_length=64, unique=True)),
                ('token_hash', models.CharField(db_index=True, max_length=64, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_activity', models.DateTimeField(default=django.utils.timezone.now)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='active_session', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Sessão de Usuário',
                'verbose_name_plural': 'Sessões de Usuários',
                'db_table': 'user_sessions',
            },
        ),
        migrations.AddIndex(
            model_name='usersession',
            index=models.Index(fields=['user', 'token_hash'], name='user_sessio_user_id_b8e9a5_idx'),
        ),
        migrations.AddIndex(
            model_name='usersession',
            index=models.Index(fields=['last_activity'], name='user_sessio_last_ac_c4f8d2_idx'),
        ),
    ]
