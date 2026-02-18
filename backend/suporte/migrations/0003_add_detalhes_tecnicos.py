# Generated manually - campo para erros do navegador e contexto técnico no chamado

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('suporte', '0002_add_tipo_chamado'),
    ]

    operations = [
        migrations.AddField(
            model_name='chamado',
            name='detalhes_tecnicos',
            field=models.TextField(blank=True, default=''),
        ),
    ]
