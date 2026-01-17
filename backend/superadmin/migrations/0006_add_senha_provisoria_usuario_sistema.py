# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0005_add_senha_alterada'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuariosistema',
            name='senha_provisoria',
            field=models.CharField(blank=True, help_text='Senha provisória gerada automaticamente', max_length=50),
        ),
        migrations.AddField(
            model_name='usuariosistema',
            name='senha_foi_alterada',
            field=models.BooleanField(default=False, help_text='Indica se o usuário já alterou a senha provisória'),
        ),
    ]
