# Generated manually - add owner_telefone to Loja

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0017_profissionalusuario_perfil'),
    ]

    operations = [
        migrations.AddField(
            model_name='loja',
            name='owner_telefone',
            field=models.CharField(blank=True, help_text='Telefone do administrador da loja', max_length=20),
        ),
    ]
