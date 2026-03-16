# Generated manually - add botao_principal_ativo to HeroSection

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('homepage', '0002_funcionalidade_icone_blank'),
    ]

    operations = [
        migrations.AddField(
            model_name='herosection',
            name='botao_principal_ativo',
            field=models.BooleanField(default=True, help_text='Exibir botão principal (ex: Testar grátis)'),
        ),
    ]
