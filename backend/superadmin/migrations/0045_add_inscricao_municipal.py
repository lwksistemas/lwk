# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0043_add_credit_card_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='loja',
            name='inscricao_municipal',
            field=models.CharField(
                blank=True,
                help_text='Inscrição municipal da loja (para emissão de NFS-e)',
                max_length=20
            ),
        ),
    ]
