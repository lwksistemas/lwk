# Generated manually - perfil de acesso do profissional (profissional | recepcao)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0016_profissionalusuario'),
    ]

    operations = [
        migrations.AddField(
            model_name='profissionalusuario',
            name='perfil',
            field=models.CharField(
                choices=[('profissional', 'Profissional (só agenda e bloqueios próprios)'), ('recepcao', 'Recepção (acesso completo: agenda, cadastros, financeiro)')],
                default='profissional',
                help_text='Profissional: só agenda própria. Recepção: acesso completo.',
                max_length=20,
            ),
        ),
    ]
