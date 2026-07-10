from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0057_nfseemitida_pdf_url_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='loja',
            name='agenda_status_colors',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Overrides de cores dos status da agenda (bg/border por status). Vazio = padrão LWK.',
            ),
        ),
    ]
