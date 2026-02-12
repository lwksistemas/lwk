# Generated manually for Bloqueio de Horários (Clínica da Beleza)

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_beleza', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BloqueioHorario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_inicio', models.DateTimeField(verbose_name='Início')),
                ('data_fim', models.DateTimeField(verbose_name='Fim')),
                ('motivo', models.CharField(max_length=100, verbose_name='Motivo')),
                ('observacoes', models.TextField(blank=True, null=True, verbose_name='Observações')),
                ('criado_em', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('professional', models.ForeignKey(blank=True, help_text='Deixe vazio para bloqueio geral (todos)', null=True, on_delete=django.db.models.deletion.CASCADE, to='clinica_beleza.professional', verbose_name='Profissional')),
            ],
            options={
                'verbose_name': 'Bloqueio de Horário',
                'verbose_name_plural': 'Bloqueios de Horário',
                'ordering': ['-data_inicio'],
            },
        ),
    ]
