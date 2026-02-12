# Generated manually for fluxo profissional Clínica da Beleza

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0015_usuariosistema_cpf'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ProfissionalUsuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('professional_id', models.PositiveIntegerField(help_text='ID do Professional no schema da loja')),
                ('precisa_trocar_senha', models.BooleanField(default=True, help_text='Obrigar troca de senha no primeiro acesso')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('loja', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='profissionais_usuarios', to='superadmin.loja')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='profissional_lojas', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Profissional (acesso)',
                'verbose_name_plural': 'Profissionais (acesso)',
            },
        ),
        migrations.AddConstraint(
            model_name='profissionalusuario',
            constraint=models.UniqueConstraint(fields=('user', 'loja'), name='superadmin_profissionalusuario_user_loja_uniq'),
        ),
        migrations.AddIndex(
            model_name='profissionalusuario',
            index=models.Index(fields=['user', 'loja'], name='prof_usuario_loja_idx'),
        ),
    ]
