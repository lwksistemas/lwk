# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('asaas_integration', '0005_superadminnfseconfig'),
    ]

    operations = [
        migrations.AddField(
            model_name='superadminnfseconfig',
            name='prestador_email',
            field=models.EmailField(blank=True, help_text='E-mail para receber notificações de NFS-e emitidas', max_length=254, verbose_name='E-mail do Prestador'),
        ),
        migrations.AddField(
            model_name='superadminnfseconfig',
            name='regime_especial_tributacao',
            field=models.CharField(blank=True, choices=[('', '-'), ('1', 'Microempresa Municipal'), ('2', 'Estimativa'), ('3', 'Sociedade de Profissionais'), ('4', 'Cooperativa'), ('5', 'Microempresário Individual (MEI)'), ('6', 'Microempresário e Empresa de Pequeno Porte (ME EPP)')], default='', help_text='Identifica o regime de tributação da empresa. Simples Nacional geralmente usa Microempresa Municipal.', max_length=2, verbose_name='Regime Especial de Tributação'),
        ),
    ]
