"""
Migration para adicionar campos do provedor Nacional (ADN) ao SuperadminNFSeConfig.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('asaas_integration', '0008_expand_nfse_config_credential_fields'),
    ]

    operations = [
        # Atualizar choices do provedor_nfse
        migrations.AlterField(
            model_name='superadminnfseconfig',
            name='provedor_nfse',
            field=models.CharField(
                choices=[
                    ('asaas', 'Asaas (Intermediário - emite via Asaas)'),
                    ('issnet', 'ISSNet Ribeirão Preto (Direto - sem taxa)'),
                    ('nacional', 'Nacional (ADN - Padrão Nacional NFS-e)'),
                    ('desabilitado', 'Desabilitado (não emite NFS-e)'),
                ],
                default='asaas',
                help_text='Como emitir notas fiscais das assinaturas das lojas',
                max_length=20,
                verbose_name='Provedor de NFS-e',
            ),
        ),
        # Certificado Nacional
        migrations.AddField(
            model_name='superadminnfseconfig',
            name='nacional_certificado',
            field=models.BinaryField(blank=True, null=True, verbose_name='Certificado Digital A1 (.pfx) - Nacional'),
        ),
        migrations.AddField(
            model_name='superadminnfseconfig',
            name='nacional_certificado_nome',
            field=models.CharField(blank=True, max_length=255, verbose_name='Nome do arquivo .pfx (Nacional)'),
        ),
        migrations.AddField(
            model_name='superadminnfseconfig',
            name='nacional_senha_certificado',
            field=models.CharField(blank=True, max_length=500, verbose_name='Senha do Certificado (Nacional)'),
        ),
        # Ambiente
        migrations.AddField(
            model_name='superadminnfseconfig',
            name='nacional_ambiente',
            field=models.CharField(
                blank=True,
                choices=[('homologacao', 'Homologação'), ('producao', 'Produção')],
                default='homologacao',
                help_text='Homologação para testes, Produção para emissão real',
                max_length=20,
                verbose_name='Ambiente Nacional',
            ),
        ),
        # Código município
        migrations.AddField(
            model_name='superadminnfseconfig',
            name='nacional_codigo_municipio',
            field=models.CharField(
                blank=True,
                help_text='Código IBGE de 7 dígitos do município do prestador',
                max_length=7,
                verbose_name='Código IBGE do Município',
            ),
        ),
        # Série DPS
        migrations.AddField(
            model_name='superadminnfseconfig',
            name='nacional_serie_dps',
            field=models.CharField(
                blank=True,
                default='900',
                help_text='Série da DPS (padrão: 900 para emissão própria)',
                max_length=5,
                verbose_name='Série da DPS',
            ),
        ),
        # Último DPS
        migrations.AddField(
            model_name='superadminnfseconfig',
            name='nacional_ultimo_dps',
            field=models.IntegerField(
                default=0,
                help_text='Próxima emissão usará este + 1',
                verbose_name='Último nº DPS emitido',
            ),
        ),
    ]
