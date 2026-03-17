# Migração manual: Adicionar titulo e tipo do BloqueioAgendaBase ao BloqueioHorario

from django.db import migrations, models


def copiar_motivo_para_titulo(apps, schema_editor):
    BloqueioHorario = apps.get_model('clinica_beleza', 'BloqueioHorario')
    for b in BloqueioHorario.objects.all():
        if b.motivo and not b.titulo:
            b.titulo = b.motivo
            b.save(update_fields=['titulo'])


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_beleza', '0013_bloqueiohorario_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='bloqueiohorario',
            name='titulo',
            field=models.CharField(
                max_length=200,
                verbose_name='Título',
                default='',
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='bloqueiohorario',
            name='tipo',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('feriado', 'Feriado'),
                    ('ferias', 'Férias'),
                    ('folga', 'Folga'),
                    ('manutencao', 'Manutenção'),
                    ('evento', 'Evento'),
                    ('outros', 'Outros'),
                ],
                verbose_name='Tipo',
                default='outros',
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='bloqueiohorario',
            name='horario_inicio',
            field=models.TimeField(
                blank=True,
                null=True,
                verbose_name='Horário Início',
                help_text='Deixe vazio para bloquear o dia todo',
            ),
        ),
        migrations.AddField(
            model_name='bloqueiohorario',
            name='horario_fim',
            field=models.TimeField(blank=True, null=True, verbose_name='Horário Fim'),
        ),
        migrations.AddField(
            model_name='bloqueiohorario',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Ativo'),
        ),
        migrations.RunPython(copiar_motivo_para_titulo, migrations.RunPython.noop),
    ]
