from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_beleza', '0057_restore_performance_indexes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='status',
            field=models.CharField(
                choices=[
                    ('PENDING', 'Pendente'),
                    ('DRAFT', 'Rascunho (consulta)'),
                    ('PAID', 'Pago'),
                    ('PARTIAL', 'Parcialmente pago'),
                    ('CANCELLED', 'Cancelado'),
                ],
                default='PENDING',
                max_length=20,
                verbose_name='Status',
            ),
        ),
    ]
