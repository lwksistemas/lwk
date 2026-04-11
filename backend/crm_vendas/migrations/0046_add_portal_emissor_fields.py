# Generated manually
"""
Adiciona campos do Portal Emissor (Asaas/Prefeitura) ao CRMConfig:
- Informações do prestador: inscricao_municipal, codigo_cnae, optante_simples_nacional,
  regime_especial_tributacao, incentivador_cultural, item_lista_servico, codigo_nbs
- Informações da NF: issnet_serie_rps, issnet_ultimo_rps_conhecido, issnet_numero_lote
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0045_add_asaas_loja_nf_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='crmconfig',
            name='inscricao_municipal',
            field=models.CharField(blank=True, help_text='Inscrição municipal do prestador (obrigatória para ISSNet)', max_length=20, verbose_name='Inscrição Municipal'),
        ),
        migrations.AddField(
            model_name='crmconfig',
            name='codigo_cnae',
            field=models.CharField(blank=True, help_text='Código CNAE da empresa (apenas números, sem formatação)', max_length=20, verbose_name='Código CNAE'),
        ),
        migrations.AddField(
            model_name='crmconfig',
            name='optante_simples_nacional',
            field=models.BooleanField(default=True, help_text='Se a empresa é enquadrada no Simples Nacional (Lei Complementar 123/2006)', verbose_name='Optante pelo Simples Nacional'),
        ),
        migrations.AddField(
            model_name='crmconfig',
            name='regime_especial_tributacao',
            field=models.CharField(blank=True, default='0', help_text='0=Nenhum, 1=Microempresa Municipal, 2=Estimativa, 3=Sociedade de Profissionais, 4=Cooperativa, 5=MEI, 6=ME/EPP Simples Nacional', max_length=2, verbose_name='Regime Especial de Tributação'),
        ),
        migrations.AddField(
            model_name='crmconfig',
            name='incentivador_cultural',
            field=models.BooleanField(default=False, help_text='Se a empresa é incentivadora cultural', verbose_name='Incentivador Cultural'),
        ),
        migrations.AddField(
            model_name='crmconfig',
            name='item_lista_servico',
            field=models.CharField(blank=True, help_text='Item da lista de serviço com formatação (ex: 17.02, 08.02)', max_length=10, verbose_name='Item da Lista de Serviços'),
        ),
        migrations.AddField(
            model_name='crmconfig',
            name='codigo_nbs',
            field=models.CharField(blank=True, help_text='Código NBS - Nomenclatura Brasileira de Serviços (opcional)', max_length=20, verbose_name='Código NBS'),
        ),
        migrations.AddField(
            model_name='crmconfig',
            name='issnet_serie_rps',
            field=models.CharField(blank=True, default='', help_text='Série utilizada para emissão (ex: NFSE, 1, E). Vazio = A', max_length=10, verbose_name='Série do RPS / Série da NF'),
        ),
        migrations.AddField(
            model_name='crmconfig',
            name='issnet_ultimo_rps_conhecido',
            field=models.IntegerField(default=0, help_text='Número do RPS da última NF emitida. Próxima emissão usará este + 1', verbose_name='Último RPS emitido'),
        ),
        migrations.AddField(
            model_name='crmconfig',
            name='issnet_numero_lote',
            field=models.IntegerField(default=0, help_text='Número do lote atual (opcional, se vazio usa mesmo número do RPS)', verbose_name='Número do Lote'),
        ),
    ]
