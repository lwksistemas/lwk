# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('homepage', '0003_herosection_botao_principal_ativo'),
    ]

    operations = [
        migrations.AddField(
            model_name='funcionalidade',
            name='imagem',
            field=models.URLField(blank=True, help_text='URL da imagem da funcionalidade (opcional, substitui ícone)', max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='herosection',
            name='imagem',
            field=models.URLField(blank=True, help_text='URL da imagem do hero (opcional)', max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='modulosistema',
            name='imagem',
            field=models.URLField(blank=True, help_text='URL da imagem do módulo (opcional, substitui ícone)', max_length=500, null=True),
        ),
    ]
