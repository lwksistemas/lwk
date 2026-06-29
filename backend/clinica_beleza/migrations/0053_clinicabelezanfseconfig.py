"""Configuração de NFS-e individual por loja (Clínica da Beleza)."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_beleza', '0052_professional_is_profissional'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClinicaBelezaNFSeConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.IntegerField(db_index=True, help_text='ID da loja proprietária deste registro')),
                ('provedor_nf', models.CharField(choices=[('asaas', 'Asaas (Intermediário - Padrão)'), ('issnet', 'ISSNet - Ribeirão Preto (Direto)'), ('nacional', 'API Nacional NFS-e (Direto)'), ('manual', 'Emissão Manual (Sem integração)')], default='asaas', max_length=20, verbose_name='Provedor de Nota Fiscal')),
                ('issnet_usuario', models.CharField(blank=True, max_length=100, verbose_name='Usuário ISSNet')),
                ('issnet_senha', models.CharField(blank=True, max_length=100, verbose_name='Senha ISSNet')),
                ('issnet_certificado', models.BinaryField(blank=True, null=True, verbose_name='Certificado Digital A1 (.pfx)')),
                ('issnet_certificado_nome', models.CharField(blank=True, max_length=255, verbose_name='Nome do arquivo .pfx')),
                ('issnet_senha_certificado', models.CharField(blank=True, max_length=100, verbose_name='Senha do Certificado')),
                ('issnet_ambiente_homologacao', models.BooleanField(default=False, verbose_name='ISSNet homologação (teste)')),
                ('inscricao_municipal', models.CharField(blank=True, max_length=20, verbose_name='Inscrição Municipal')),
                ('codigo_cnae', models.CharField(blank=True, max_length=20, verbose_name='Código CNAE')),
                ('optante_simples_nacional', models.BooleanField(default=True, verbose_name='Optante pelo Simples Nacional')),
                ('regime_especial_tributacao', models.CharField(blank=True, default='0', max_length=2, verbose_name='Regime Especial de Tributação')),
                ('incentivador_cultural', models.BooleanField(default=False, verbose_name='Incentivador Cultural')),
                ('item_lista_servico', models.CharField(blank=True, max_length=10, verbose_name='Item da Lista de Serviços (LC 116)')),
                ('codigo_nbs', models.CharField(blank=True, max_length=20, verbose_name='Código NBS')),
                ('issnet_serie_rps', models.CharField(blank=True, default='', max_length=10, verbose_name='Série do RPS')),
                ('issnet_ultimo_rps_conhecido', models.IntegerField(default=0, verbose_name='Último RPS emitido')),
                ('issnet_numero_lote', models.IntegerField(default=0, verbose_name='Número do Lote')),
                ('codigo_servico_municipal', models.CharField(default='0601', max_length=10, verbose_name='Código do Serviço Municipal')),
                ('descricao_servico_padrao', models.TextField(default='Serviços de estética, saúde e bem-estar', verbose_name='Descrição Padrão do Serviço')),
                ('aliquota_iss', models.DecimalField(decimal_places=2, default=2.00, max_digits=5, verbose_name='Alíquota ISS (%)')),
                ('emitir_nf_automaticamente', models.BooleanField(default=True, verbose_name='Emitir NF Automaticamente')),
                ('asaas_api_key', models.CharField(blank=True, max_length=255, verbose_name='API Key Asaas (loja)')),
                ('asaas_sandbox', models.BooleanField(default=False, verbose_name='Asaas sandbox (homologação)')),
                ('asaas_webhook_token', models.TextField(blank=True, default='', verbose_name='Token webhook Asaas (loja)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'clinica_beleza_nfse_config',
                'verbose_name': 'Configuração NFS-e (Clínica)',
                'verbose_name_plural': 'Configurações NFS-e (Clínicas)',
                'indexes': [
                    models.Index(fields=['loja_id'], name='clinica_bel_loja_id_nfse_idx'),
                ],
            },
        ),
    ]
