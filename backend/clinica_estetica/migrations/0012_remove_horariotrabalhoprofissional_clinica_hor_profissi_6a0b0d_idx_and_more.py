# Ajuste de índices e help_text de loja_id (alinhado ao LojaIsolationMixin)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_estetica', '0011_horario_trabalho_profissional'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='horariotrabalhoprofissional',
            name='clinica_hor_profissi_6a0b0d_idx',
        ),
        migrations.RemoveIndex(
            model_name='horariotrabalhoprofissional',
            name='clinica_hor_loja_id_8c1e2f_idx',
        ),
        migrations.AlterField(
            model_name='horariotrabalhoprofissional',
            name='loja_id',
            field=models.IntegerField(
                db_index=True,
                help_text='ID da loja proprietária deste registro',
            ),
        ),
    ]
