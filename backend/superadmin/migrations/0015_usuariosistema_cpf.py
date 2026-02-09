# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0014_alter_loja_options_alter_planoassinatura_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuariosistema',
            name='cpf',
            field=models.CharField(blank=True, help_text='CPF do usuário (apenas números ou formatado)', max_length=14),
        ),
    ]
