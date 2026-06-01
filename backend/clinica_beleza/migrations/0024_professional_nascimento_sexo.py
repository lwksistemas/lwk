from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_beleza', '0023_prescricao_memed'),
    ]

    operations = [
        migrations.AddField(
            model_name='professional',
            name='data_nascimento',
            field=models.DateField(
                blank=True, null=True, verbose_name='Data de nascimento',
                help_text='Data de nascimento do prescritor (usada no cadastro da Memed).',
            ),
        ),
        migrations.AddField(
            model_name='professional',
            name='sexo',
            field=models.CharField(
                blank=True, null=True, max_length=1,
                choices=[('M', 'Masculino'), ('F', 'Feminino')],
                verbose_name='Sexo',
                help_text='Sexo do prescritor (usado no cadastro da Memed).',
            ),
        ),
    ]
