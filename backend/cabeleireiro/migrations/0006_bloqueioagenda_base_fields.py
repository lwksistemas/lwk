# Migração manual: Adicionar campos do BloqueioAgendaBase ao BloqueioAgenda

from django.db import migrations, models
from django.utils import timezone


def copiar_motivo_para_titulo(apps, schema_editor):
    BloqueioAgenda = apps.get_model('cabeleireiro', 'BloqueioAgenda')
    for b in BloqueioAgenda.objects.all():
        if b.motivo and not b.titulo:
            b.titulo = b.motivo
            b.save(update_fields=['titulo'])


class Migration(migrations.Migration):

    dependencies = [
        ('cabeleireiro', '0005_alter_profissional_options_alter_agendamento_loja_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='bloqueioagenda',
            name='titulo',
            field=models.CharField(
                max_length=200,
                verbose_name='Título',
                default='',
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='bloqueioagenda',
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
            model_name='bloqueioagenda',
            name='horario_inicio',
            field=models.TimeField(
                blank=True,
                null=True,
                verbose_name='Horário Início',
                help_text='Deixe vazio para bloquear o dia todo',
            ),
        ),
        migrations.AddField(
            model_name='bloqueioagenda',
            name='horario_fim',
            field=models.TimeField(blank=True, null=True, verbose_name='Horário Fim'),
        ),
        migrations.AddField(
            model_name='bloqueioagenda',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Ativo'),
        ),
        migrations.AddField(
            model_name='bloqueioagenda',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True,
                verbose_name='Criado em',
                default=timezone.now,
            ),
            preserve_default=False,
        ),
        migrations.RunPython(copiar_motivo_para_titulo, migrations.RunPython.noop),
    ]
