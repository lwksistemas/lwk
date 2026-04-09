# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0030_add_contato_to_lead'),
    ]

    operations = [
        migrations.AddField(
            model_name='crmconfig',
            name='provedor_nf',
            field=models.CharField(
                choices=[
                    ('asaas', 'Asaas (Intermediário - Padrão)'),
                    ('issnet', 'ISSNet - Ribeirão Preto (Direto)'),
                    ('nacional', 'API Nacional NFS-e (Direto)'),
                    ('manual', 'Emissão Manual (Sem integração)')
                ],
                default='asaas',
                help_text='Sistema usado para emitir notas fiscais de serviço',
                max_length=20,
                verbose_name='Provedor de Nota Fiscal'
            ),
        ),
        migrations.AddField(
            model_name='crmconfig',
            name='issnet_usuario',
            field=models.CharField(
                blank=True,
                help_text='Usuário de acesso ao webservice ISSNet',
                max_length=100,
                verbose_name='Usuário ISSNet'
            ),
        ),
        migrations.AddField(
            model_name='crmconfig',
            name='issnet_senha',
            field=models.CharField(
                blank=True,
                help_text='Senha de acesso ao webservice ISSNet',
                max_length=100,
                verbose_name='Senha ISSNet'
            ),
        ),
        migrations.AddField(
            model_name='crmconfig',
            name='issnet_certificado',
            field=models.FileField(
                blank=True,
                help_text='Arquivo .pfx do certificado digital A1 (e-CNPJ)',
                null=True,
                upload_to='certificados_nfse/%Y/%m/',
                verbose_name='Certificado Digital A1'
            ),
        ),
        migrations.AddField(
            model_name='crmconfig',
            name='issnet_senha_certificado',
            field=models.CharField(
                blank=True,
                help_text='Senha do arquivo .pfx do certificado digital',
                max_length=100,
                verbose_name='Senha do Certificado'
            ),
        ),
        migrations.AddField(
            model_name='crmconfig',
            name='codigo_servico_municipal',
            field=models.CharField(
                default='1401',
                help_text='Código do serviço na lista de serviços do município (ex: 1401)',
                max_length=10,
                verbose_name='Código do Serviço Municipal'
            ),
        ),
        migrations.AddField(
            model_name='crmconfig',
            name='descricao_servico_padrao',
            field=models.TextField(
                default='Desenvolvimento e licenciamento de software sob demanda',
                help_text='Descrição que aparecerá nas notas fiscais emitidas',
                verbose_name='Descrição Padrão do Serviço'
            ),
        ),
        migrations.AddField(
            model_name='crmconfig',
            name='aliquota_iss',
            field=models.DecimalField(
                decimal_places=2,
                default=2.00,
                help_text='Alíquota do ISS aplicada (geralmente 2% a 5%)',
                max_digits=5,
                verbose_name='Alíquota ISS (%)'
            ),
        ),
        migrations.AddField(
            model_name='crmconfig',
            name='emitir_nf_automaticamente',
            field=models.BooleanField(
                default=True,
                help_text='Emitir nota fiscal automaticamente ao confirmar pagamento',
                verbose_name='Emitir NF Automaticamente'
            ),
        ),
    ]
