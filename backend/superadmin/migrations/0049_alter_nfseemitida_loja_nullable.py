import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0048_nfseemitida'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nfseemitida',
            name='loja',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='nfse_emitidas',
                to='superadmin.loja',
            ),
        ),
    ]
