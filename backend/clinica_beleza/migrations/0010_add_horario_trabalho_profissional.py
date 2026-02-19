# Horários de trabalho por profissional (dias e horários configuráveis)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_beleza', '0009_add_performance_indexes'),
    ]

    operations = [
        migrations.CreateModel(
            name='HorarioTrabalhoProfissional',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.PositiveIntegerField(db_index=True, editable=False, null=True)),
                ('dia_semana', models.IntegerField(
                    choices=[
                        (0, 'Segunda-feira'),
                        (1, 'Terça-feira'),
                        (2, 'Quarta-feira'),
                        (3, 'Quinta-feira'),
                        (4, 'Sexta-feira'),
                        (5, 'Sábado'),
                        (6, 'Domingo'),
                    ],
                    verbose_name='Dia da semana',
                )),
                ('hora_entrada', models.TimeField(verbose_name='Entrada')),
                ('hora_saida', models.TimeField(verbose_name='Saída')),
                ('intervalo_inicio', models.TimeField(
                    blank=True,
                    null=True,
                    verbose_name='Início intervalo (ex.: almoço)',
                    help_text='Opcional',
                )),
                ('intervalo_fim', models.TimeField(
                    blank=True,
                    null=True,
                    verbose_name='Fim intervalo',
                    help_text='Opcional',
                )),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),
                ('professional', models.ForeignKey(
                    on_delete=models.CASCADE,
                    related_name='horarios_trabalho',
                    to='clinica_beleza.professional',
                    verbose_name='Profissional',
                )),
            ],
            options={
                'verbose_name': 'Horário de trabalho (profissional)',
                'verbose_name_plural': 'Horários de trabalho (profissionais)',
                'ordering': ['professional', 'dia_semana'],
                'app_label': 'clinica_beleza',
                'unique_together': {('professional', 'dia_semana')},
            },
        ),
        migrations.AddIndex(
            model_name='horariotrabalhoprofissional',
            index=models.Index(fields=['professional', 'dia_semana'], name='clinica_be_prof_ds_idx'),
        ),
        migrations.AddIndex(
            model_name='horariotrabalhoprofissional',
            index=models.Index(fields=['loja_id', 'professional'], name='clinica_be_loja_pr_idx'),
        ),
    ]
