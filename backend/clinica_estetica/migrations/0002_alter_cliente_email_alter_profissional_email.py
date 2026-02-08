# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_estetica', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cliente',
            name='email',
            field=models.EmailField(blank=True, null=True, max_length=254),
        ),
        migrations.AlterField(
            model_name='profissional',
            name='email',
            field=models.EmailField(blank=True, null=True, max_length=254),
        ),
    ]
