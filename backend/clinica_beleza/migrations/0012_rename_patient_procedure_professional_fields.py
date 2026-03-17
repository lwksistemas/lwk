# Migração manual: Renomear campos para compatibilidade com ClienteBase/ServicoBase/ProfissionalBase

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_beleza', '0011_remove_appointment_clinica_bel_loja_id_appt_idx_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='patient',
            old_name='birth_date',
            new_name='data_nascimento',
        ),
        migrations.RenameField(
            model_name='patient',
            old_name='address',
            new_name='endereco',
        ),
        migrations.RenameField(
            model_name='patient',
            old_name='active',
            new_name='is_active',
        ),
        migrations.RenameField(
            model_name='patient',
            old_name='notes',
            new_name='observacoes',
        ),
        migrations.RenameField(
            model_name='procedure',
            old_name='description',
            new_name='descricao',
        ),
        migrations.RenameField(
            model_name='procedure',
            old_name='active',
            new_name='is_active',
        ),
        migrations.RenameField(
            model_name='professional',
            old_name='active',
            new_name='is_active',
        ),
    ]
