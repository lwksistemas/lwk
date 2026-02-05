# Generated migration to rename duracao to duracao_minutos

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cabeleireiro', '0003_add_funcao_especialidade_comissao'),
    ]

    operations = [
        migrations.RenameField(
            model_name='servico',
            old_name='duracao',
            new_name='duracao_minutos',
        ),
    ]
