# Generated manually - Horários de atendimento por profissional (Clínica de Estética)

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_estetica', '0010_add_loja_id_to_bloqueio_agenda'),
    ]

    operations = [
        migrations.CreateModel(
            name='HorarioTrabalhoProfissional',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.IntegerField(db_index=True, help_text='ID da loja (isolamento multi-tenant)')),
                ('dia_semana', models.IntegerField(choices=[(0, 'Segunda-feira'), (1, 'Terça-feira'), (2, 'Quarta-feira'), (3, 'Quinta-feira'), (4, 'Sexta-feira'), (5, 'Sábado'), (6, 'Domingo')], verbose_name='Dia da semana')),
                ('hora_entrada', models.TimeField(verbose_name='Entrada')),
                ('hora_saida', models.TimeField(verbose_name='Saída')),
                ('intervalo_inicio', models.TimeField(blank=True, help_text='Opcional', null=True, verbose_name='Início intervalo (ex.: almoço)')),
                ('intervalo_fim', models.TimeField(blank=True, help_text='Opcional', null=True, verbose_name='Fim intervalo')),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),
                ('profissional', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='horarios_trabalho', to='clinica_estetica.profissional', verbose_name='Profissional')),
            ],
            options={
                'verbose_name': 'Horário de atendimento (profissional)',
                'verbose_name_plural': 'Horários de atendimento (profissionais)',
                'db_table': 'clinica_horarios_trabalho_profissional',
                'ordering': ['profissional', 'dia_semana'],
                'unique_together': {('profissional', 'dia_semana')},
            },
        ),
        migrations.AddIndex(
            model_name='horariotrabalhoprofissional',
            index=models.Index(fields=['profissional', 'dia_semana'], name='clinica_hor_profissi_6a0b0d_idx'),
        ),
        migrations.AddIndex(
            model_name='horariotrabalhoprofissional',
            index=models.Index(fields=['loja_id', 'profissional'], name='clinica_hor_loja_id_8c1e2f_idx'),
        ),
    ]
