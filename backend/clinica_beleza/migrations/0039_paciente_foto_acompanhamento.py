# Fotos de acompanhamento do paciente (QR + painel)
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_beleza', '0038_termo_por_procedimento'),
    ]

    operations = [
        migrations.CreateModel(
            name='PacienteFotoAcompanhamento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.IntegerField(db_index=True)),
                ('cloudinary_url', models.URLField(max_length=500)),
                ('cloudinary_public_id', models.CharField(blank=True, default='', max_length=255)),
                ('origem', models.CharField(
                    choices=[('qr', 'QR / Celular'), ('painel', 'Painel da consulta')],
                    default='qr',
                    max_length=10,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('consulta', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='fotos_paciente',
                    to='clinica_beleza.consulta',
                )),
                ('patient', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='fotos_acompanhamento',
                    to='clinica_beleza.patient',
                )),
            ],
            options={
                'verbose_name': 'Foto de acompanhamento',
                'verbose_name_plural': 'Fotos de acompanhamento',
                'db_table': 'clinica_beleza_paciente_fotos',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='pacientefotoacompanhamento',
            index=models.Index(fields=['patient', 'created_at'], name='clin_cb_foto_pac_dt_idx'),
        ),
        migrations.AddIndex(
            model_name='pacientefotoacompanhamento',
            index=models.Index(fields=['consulta'], name='clin_cb_foto_cons_idx'),
        ),
    ]
