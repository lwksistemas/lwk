"""
Migration para criar tabela de configuração NFS-e do Superadmin.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('asaas_integration', '0004_asaasconfig'),
    ]

    operations = [
        migrations.CreateModel(
            name='SuperadminNFSeConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('singleton_key', models.CharField(default='config', max_length=10, unique=True)),
                ('provedor_nfse', models.CharField(choices=[('asaas', 'Asaas (Intermediário - emite via Asaas)'), ('issnet', 'ISSNet Ribeirão Preto (Direto - sem taxa)'), ('desabilitado', 'Desabilitado (não emite NFS-e)')], default='asaas', help_text='Como emitir notas fiscais das assinaturas das lojas', max_length=20, verbose_name='Provedor de NFS-e')),
                ('emitir_automaticamente', models.BooleanField(default=True, help_text='Emitir NFS-e automaticamente quando pagamento é confirmado', verbose_name='Emitir automaticamente')),
                ('prestador_cnpj', models.CharField(blank=True, help_text='CNPJ da empresa que emite as notas (ex: LWK Sistemas)', max_length=18, verbose_name='CNPJ do Prestador')),
                ('prestador_razao_social', models.CharField(blank=True, max_length=200, verbose_name='Razão Social')),
                ('prestador_inscricao_municipal', models.CharField(blank=True, max_length=20, verbose_name='Inscrição Municipal')),
                ('issnet_usuario', models.CharField(blank=True, max_length=100, verbose_name='Usuário ISSNet')),
                ('issnet_senha', models.CharField(blank=True, max_length=100, verbose_name='Senha ISSNet')),
                ('issnet_certificado', models.BinaryField(blank=True, null=True, verbose_name='Certificado Digital A1 (.pfx)')),
                ('issnet_certificado_nome', models.CharField(blank=True, max_length=255, verbose_name='Nome do arquivo .pfx')),
                ('issnet_senha_certificado', models.CharField(blank=True, max_length=100, verbose_name='Senha do Certificado')),
                ('codigo_servico_municipal', models.CharField(blank=True, default='1401', max_length=10, verbose_name='Código do Serviço Municipal')),
                ('descricao_servico_padrao', models.TextField(blank=True, default='Licenciamento de uso de software SaaS', verbose_name='Descrição Padrão do Serviço')),
                ('aliquota_iss', models.DecimalField(decimal_places=2, default=2.0, max_digits=5, verbose_name='Alíquota ISS (%)')),
                ('codigo_cnae', models.CharField(blank=True, max_length=20, verbose_name='Código CNAE')),
                ('optante_simples_nacional', models.BooleanField(default=True, verbose_name='Optante Simples Nacional')),
                ('serie_rps', models.CharField(blank=True, default='E', max_length=10, verbose_name='Série do RPS')),
                ('ultimo_rps', models.IntegerField(default=0, help_text='Próxima emissão usará este + 1', verbose_name='Último RPS emitido')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Configuração NFS-e Superadmin',
                'verbose_name_plural': 'Configurações NFS-e Superadmin',
                'db_table': 'superadmin_nfse_config',
            },
        ),
    ]
