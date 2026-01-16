# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0004_add_senha_provisoria'),
    ]

    operations = [
        migrations.AddField(
            model_name='loja',
            name='senha_foi_alterada',
            field=models.BooleanField(default=False, help_text='Indica se o proprietário já alterou a senha provisória'),
        ),
    ]
