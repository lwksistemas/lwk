"""
Adiciona campos xml_dps_assinado e resposta_adn ao NFSeEmitida
para debug da integração NFS-e Nacional (ADN).
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0053_googlecalendar_loja_fk_state_only'),
    ]

    operations = [
        migrations.AddField(
            model_name='nfseemitida',
            name='xml_dps_assinado',
            field=models.TextField(
                blank=True,
                default='',
                help_text='XML completo assinado enviado ao ADN — para validação manual',
                verbose_name='XML DPS Assinado (debug)',
            ),
        ),
        migrations.AddField(
            model_name='nfseemitida',
            name='resposta_adn',
            field=models.TextField(
                blank=True,
                default='',
                help_text='Resposta JSON completa retornada pelo ADN — para diagnóstico',
                verbose_name='Resposta ADN (debug)',
            ),
        ),
    ]
