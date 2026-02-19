# Generated manually for performance optimization
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_beleza', '0008_campanha_promocao'),
    ]

    operations = [
        # Índices para Appointment
        migrations.AddIndex(
            model_name='appointment',
            index=models.Index(fields=['date', 'status'], name='clinica_be_date_st_idx'),
        ),
        migrations.AddIndex(
            model_name='appointment',
            index=models.Index(fields=['professional', 'date'], name='clinica_be_prof_da_idx'),
        ),
        migrations.AddIndex(
            model_name='appointment',
            index=models.Index(fields=['patient', 'date'], name='clinica_be_pat_dat_idx'),
        ),
        migrations.AddIndex(
            model_name='appointment',
            index=models.Index(fields=['loja_id', 'date'], name='clinica_be_loja_da_idx'),
        ),
        
        # Índices para BloqueioHorario
        migrations.AddIndex(
            model_name='bloqueiohorario',
            index=models.Index(fields=['data_inicio', 'data_fim'], name='clinica_be_data_in_idx'),
        ),
        migrations.AddIndex(
            model_name='bloqueiohorario',
            index=models.Index(fields=['professional', 'data_inicio'], name='clinica_be_prof_di_idx'),
        ),
        migrations.AddIndex(
            model_name='bloqueiohorario',
            index=models.Index(fields=['loja_id', 'data_inicio'], name='clinica_be_loja_di_idx'),
        ),
        
        # Índices para Payment
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['status', 'payment_date'], name='clinica_be_stat_pa_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['appointment', 'status'], name='clinica_be_appt_st_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['loja_id', 'payment_date'], name='clinica_be_loja_pa_idx'),
        ),
    ]
