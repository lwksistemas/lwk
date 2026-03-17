# Migração manual: Renomear name/phone/specialty e adicionar categoria

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_beleza', '0014_bloqueiohorario_titulo_tipo'),
    ]

    operations = [
        migrations.RenameField(
            model_name='patient',
            old_name='name',
            new_name='nome',
        ),
        migrations.RenameField(
            model_name='patient',
            old_name='phone',
            new_name='telefone',
        ),
        migrations.AddField(
            model_name='patient',
            name='cidade',
            field=models.CharField(max_length=100, blank=True, null=True, verbose_name='Cidade'),
        ),
        migrations.AddField(
            model_name='patient',
            name='estado',
            field=models.CharField(max_length=2, blank=True, null=True, verbose_name='Estado'),
        ),
        migrations.RenameField(
            model_name='procedure',
            old_name='name',
            new_name='nome',
        ),
        migrations.RenameField(
            model_name='procedure',
            old_name='price',
            new_name='preco',
        ),
        migrations.RenameField(
            model_name='procedure',
            old_name='duration',
            new_name='duracao_minutos',
        ),
        migrations.AddField(
            model_name='procedure',
            name='categoria',
            field=models.CharField(
                max_length=100,
                verbose_name='Categoria',
                default='Geral',
            ),
            preserve_default=False,
        ),
        migrations.RenameField(
            model_name='professional',
            old_name='name',
            new_name='nome',
        ),
        migrations.RenameField(
            model_name='professional',
            old_name='phone',
            new_name='telefone',
        ),
        migrations.RenameField(
            model_name='professional',
            old_name='specialty',
            new_name='especialidade',
        ),
        migrations.AddField(
            model_name='professional',
            name='comissao_percentual',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
                max_digits=5,
                verbose_name='Comissão %',
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='professional',
            name='registro_profissional',
            field=models.CharField(
                max_length=50,
                blank=True,
                null=True,
                verbose_name='Registro Profissional',
            ),
        ),
    ]
