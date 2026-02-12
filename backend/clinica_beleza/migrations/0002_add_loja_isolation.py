# Generated manually for adding LojaIsolationMixin

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_beleza', '0001_initial'),
    ]

    operations = [
        # Adicionar campo loja_id em Patient
        migrations.AddField(
            model_name='patient',
            name='loja_id',
            field=models.IntegerField(db_index=True, default=0, help_text='ID da loja proprietária deste registro'),
            preserve_default=False,
        ),
        
        # Adicionar campo loja_id em Professional
        migrations.AddField(
            model_name='professional',
            name='loja_id',
            field=models.IntegerField(db_index=True, default=0, help_text='ID da loja proprietária deste registro'),
            preserve_default=False,
        ),
        
        # Adicionar campo loja_id em Procedure
        migrations.AddField(
            model_name='procedure',
            name='loja_id',
            field=models.IntegerField(db_index=True, default=0, help_text='ID da loja proprietária deste registro'),
            preserve_default=False,
        ),
        
        # Adicionar campo loja_id em Appointment
        migrations.AddField(
            model_name='appointment',
            name='loja_id',
            field=models.IntegerField(db_index=True, default=0, help_text='ID da loja proprietária deste registro'),
            preserve_default=False,
        ),
        
        # Adicionar campo loja_id em BloqueioHorario
        migrations.AddField(
            model_name='bloqueiohorario',
            name='loja_id',
            field=models.IntegerField(db_index=True, default=0, help_text='ID da loja proprietária deste registro'),
            preserve_default=False,
        ),
        
        # Adicionar campo loja_id em Payment
        migrations.AddField(
            model_name='payment',
            name='loja_id',
            field=models.IntegerField(db_index=True, default=0, help_text='ID da loja proprietária deste registro'),
            preserve_default=False,
        ),
        
        # Adicionar índices
        migrations.AddIndex(
            model_name='patient',
            index=models.Index(fields=['loja_id'], name='clinica_bel_loja_id_patient_idx'),
        ),
        migrations.AddIndex(
            model_name='professional',
            index=models.Index(fields=['loja_id'], name='clinica_bel_loja_id_prof_idx'),
        ),
        migrations.AddIndex(
            model_name='procedure',
            index=models.Index(fields=['loja_id'], name='clinica_bel_loja_id_proc_idx'),
        ),
        migrations.AddIndex(
            model_name='appointment',
            index=models.Index(fields=['loja_id'], name='clinica_bel_loja_id_appt_idx'),
        ),
        migrations.AddIndex(
            model_name='bloqueiohorario',
            index=models.Index(fields=['loja_id'], name='clinica_bel_loja_id_bloq_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['loja_id'], name='clinica_bel_loja_id_pay_idx'),
        ),
    ]
