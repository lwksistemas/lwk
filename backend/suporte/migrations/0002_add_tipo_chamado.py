# Generated manually on 2026-01-17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('suporte', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='chamado',
            name='tipo',
            field=models.CharField(
                choices=[
                    ('duvida', 'Dúvida'),
                    ('treinamento', 'Treinamento'),
                    ('problema', 'Problema Técnico'),
                    ('sugestao', 'Sugestão'),
                    ('outro', 'Outro')
                ],
                default='duvida',
                max_length=20
            ),
        ),
    ]
