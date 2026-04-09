# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('superadmin', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='NFSe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.IntegerField(db_index=True, help_text='ID da loja (isolamento de dados)')),
                ('numero_nf', models.CharField(help_text='Número da nota fiscal gerado pela prefeitura', max_length=50, verbose_name='Número da NFS-e')),
                ('numero_rps', models.IntegerField(default=0, help_text='Número do Recibo Provisório de Serviços', verbose_name='Número do RPS')),
                ('codigo_verificacao', models.CharField(blank=True, help_text='Código para verificar autenticidade da NF no portal da prefeitura', max_length=50, verbose_name='Código de Verificação')),
                ('data_emissao', models.DateTimeField(help_text='Data e hora em que a NF foi emitida', verbose_name='Data de Emissão')),
                ('data_cancelamento', models.DateTimeField(blank=True, help_text='Data e hora em que a NF foi cancelada', null=True, verbose_name='Data de Cancelamento')),
                ('valor', models.DecimalField(decimal_places=2, default=0, help_text='Valor total dos serviços', max_digits=10, verbose_name='Valor Total')),
                ('valor_iss', models.DecimalField(decimal_places=2, default=0, help_text='Valor do ISS retido', max_digits=10, verbose_name='Valor ISS')),
                ('aliquota_iss', models.DecimalField(decimal_places=2, default=0, help_text='Alíquota do ISS aplicada', max_digits=5, verbose_name='Alíquota ISS (%)')),
                ('tomador_cpf_cnpj', models.CharField(blank=True, help_text='CPF ou CNPJ do cliente', max_length=18, verbose_name='CPF/CNPJ do Tomador')),
                ('tomador_nome', models.CharField(blank=True, help_text='Nome ou razão social do cliente', max_length=200, verbose_name='Nome do Tomador')),
                ('tomador_email', models.EmailField(blank=True, help_text='Email do cliente', max_length=254, verbose_name='Email do Tomador')),
                ('servico_codigo', models.CharField(blank=True, help_text='Código do serviço municipal', max_length=10, verbose_name='Código do Serviço')),
                ('servico_descricao', models.TextField(blank=True, help_text='Descrição do serviço prestado', verbose_name='Descrição do Serviço')),
                ('provedor', models.CharField(choices=[('asaas', 'Asaas'), ('issnet', 'ISSNet - Ribeirão Preto'), ('nacional', 'API Nacional NFS-e'), ('manual', 'Manual')], default='asaas', help_text='Sistema usado para emitir a NF', max_length=20, verbose_name='Provedor')),
                ('status', models.CharField(choices=[('emitida', 'Emitida'), ('cancelada', 'Cancelada'), ('erro', 'Erro na Emissão')], default='emitida', help_text='Status atual da NF', max_length=20, verbose_name='Status')),
                ('xml_rps', models.TextField(blank=True, help_text='XML do Recibo Provisório de Serviços', verbose_name='XML do RPS')),
                ('xml_nfse', models.TextField(blank=True, help_text='XML da Nota Fiscal de Serviço Eletrônica', verbose_name='XML da NFS-e')),
                ('pdf_url', models.URLField(blank=True, help_text='URL para download do PDF da NF', verbose_name='URL do PDF')),
                ('xml_url', models.URLField(blank=True, help_text='URL para download do XML da NF', verbose_name='URL do XML')),
                ('observacoes', models.TextField(blank=True, help_text='Observações internas sobre a NF', verbose_name='Observações')),
                ('erro', models.TextField(blank=True, help_text='Mensagem de erro se a emissão falhou', verbose_name='Erro')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'NFS-e',
                'verbose_name_plural': 'NFS-e',
                'db_table': 'nfse_integration_nfse',
                'ordering': ['-data_emissao'],
                'unique_together': {('loja_id', 'numero_nf')},
                'indexes': [
                    models.Index(fields=['loja_id', '-data_emissao'], name='nfse_loja_data_idx'),
                    models.Index(fields=['numero_nf'], name='nfse_numero_idx'),
                    models.Index(fields=['numero_rps'], name='nfse_rps_idx'),
                    models.Index(fields=['status'], name='nfse_status_idx'),
                    models.Index(fields=['tomador_cpf_cnpj'], name='nfse_tomador_idx'),
                ],
            },
        ),
    ]
