from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nfse_integration', '0003_alter_nfse_loja_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nfse',
            name='pdf_url',
            field=models.TextField(
                blank=True,
                help_text='URL para download do PDF da NF',
                verbose_name='URL do PDF',
            ),
        ),
        migrations.AlterField(
            model_name='nfse',
            name='xml_url',
            field=models.TextField(
                blank=True,
                help_text='URL para download do XML da NF',
                verbose_name='URL do XML',
            ),
        ),
    ]
