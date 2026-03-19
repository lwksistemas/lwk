# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0026_add_numero_proposta'),
    ]

    operations = [
        migrations.AddField(
            model_name='conta',
            name='razao_social',
            field=models.CharField(blank=True, help_text='Razão social da empresa', max_length=255),
        ),
        migrations.AddField(
            model_name='conta',
            name='cnpj',
            field=models.CharField(blank=True, help_text='CNPJ da empresa (formato: 00.000.000/0000-00)', max_length=18),
        ),
        migrations.AddField(
            model_name='conta',
            name='inscricao_estadual',
            field=models.CharField(blank=True, help_text='Inscrição estadual', max_length=20),
        ),
        migrations.AddField(
            model_name='conta',
            name='site',
            field=models.URLField(blank=True, help_text='Website da empresa', null=True),
        ),
        migrations.AddField(
            model_name='conta',
            name='cep',
            field=models.CharField(blank=True, help_text='CEP (formato: 00000-000)', max_length=10),
        ),
        migrations.AddField(
            model_name='conta',
            name='logradouro',
            field=models.CharField(blank=True, help_text='Rua, avenida, etc.', max_length=255),
        ),
        migrations.AddField(
            model_name='conta',
            name='numero',
            field=models.CharField(blank=True, help_text='Número do endereço', max_length=20),
        ),
        migrations.AddField(
            model_name='conta',
            name='complemento',
            field=models.CharField(blank=True, help_text='Complemento (apto, sala, etc.)', max_length=100),
        ),
        migrations.AddField(
            model_name='conta',
            name='bairro',
            field=models.CharField(blank=True, help_text='Bairro', max_length=100),
        ),
        migrations.AddField(
            model_name='conta',
            name='uf',
            field=models.CharField(blank=True, help_text='Estado (UF)', max_length=2),
        ),
        migrations.AlterField(
            model_name='conta',
            name='nome',
            field=models.CharField(help_text='Nome fantasia da empresa', max_length=255),
        ),
        migrations.AlterField(
            model_name='conta',
            name='endereco',
            field=models.CharField(blank=True, help_text='Endereço completo (campo legado)', max_length=255),
        ),
        migrations.AlterField(
            model_name='conta',
            name='cidade',
            field=models.CharField(blank=True, help_text='Cidade', max_length=100),
        ),
    ]
