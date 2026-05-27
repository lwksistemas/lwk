"""
Migration para criar modelo RelatorioComissao.
"""
import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0057_atividade_conta_atividade_crm_ativ_loja_conta_idx'),
    ]

    operations = [
        migrations.CreateModel(
            name='RelatorioComissao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.IntegerField(db_index=True)),
                ('numero', models.CharField(blank=True, help_text='Número sequencial (ex: RC-2024-001)', max_length=20)),
                ('titulo', models.CharField(help_text='Título descritivo', max_length=255)),
                ('periodo_inicio', models.DateField()),
                ('periodo_fim', models.DateField()),
                ('periodo_descricao', models.CharField(blank=True, max_length=100)),
                ('valor_total_vendas', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('valor_total_comissao', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('quantidade_vendas', models.IntegerField(default=0)),
                ('status', models.CharField(choices=[('pendente_aprovacao', 'Aguardando aprovação da empresa'), ('reprovado', 'Reprovado pela empresa'), ('aprovado', 'Aprovado — aguardando assinatura do vendedor'), ('aguardando_pagamento', 'Aguardando pagamento'), ('pago', 'Pago'), ('nfse_emitida', 'NFS-e emitida'), ('concluido', 'Concluído'), ('cancelado', 'Cancelado')], db_index=True, default='pendente_aprovacao', max_length=30)),
                ('token_empresa', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('token_vendedor', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('empresa_aprovado_em', models.DateTimeField(blank=True, null=True)),
                ('empresa_aprovado_ip', models.GenericIPAddressField(blank=True, null=True)),
                ('empresa_aprovado_nome', models.CharField(blank=True, max_length=200)),
                ('empresa_reprovado_em', models.DateTimeField(blank=True, null=True)),
                ('empresa_reprovado_motivo', models.TextField(blank=True)),
                ('vendedor_assinado_em', models.DateTimeField(blank=True, null=True)),
                ('vendedor_assinado_ip', models.GenericIPAddressField(blank=True, null=True)),
                ('vendedor_assinado_nome', models.CharField(blank=True, max_length=200)),
                ('asaas_payment_id', models.CharField(blank=True, max_length=100)),
                ('asaas_customer_id', models.CharField(blank=True, max_length=100)),
                ('boleto_url', models.URLField(blank=True)),
                ('boleto_vencimento', models.DateField(blank=True, null=True)),
                ('pago_em', models.DateTimeField(blank=True, null=True)),
                ('nfse_numero', models.CharField(blank=True, max_length=100)),
                ('nfse_emitida_em', models.DateTimeField(blank=True, null=True)),
                ('observacoes', models.TextField(blank=True)),
                ('dados_oportunidades', models.JSONField(default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('empresa_prestadora', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='relatorios_comissao', to='crm_vendas.conta')),
                ('vendedor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='relatorios_comissao', to='crm_vendas.vendedor')),
            ],
            options={
                'verbose_name': 'Relatório de Comissão',
                'verbose_name_plural': 'Relatórios de Comissão',
                'db_table': 'crm_relatorio_comissao',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='relatoriocomissao',
            index=models.Index(fields=['loja_id', 'status'], name='rc_loja_status_idx'),
        ),
        migrations.AddIndex(
            model_name='relatoriocomissao',
            index=models.Index(fields=['loja_id', 'empresa_prestadora'], name='rc_loja_empresa_idx'),
        ),
        migrations.AddIndex(
            model_name='relatoriocomissao',
            index=models.Index(fields=['loja_id', '-created_at'], name='rc_loja_created_idx'),
        ),
        migrations.AddIndex(
            model_name='relatoriocomissao',
            index=models.Index(fields=['token_empresa'], name='rc_token_empresa_idx'),
        ),
        migrations.AddIndex(
            model_name='relatoriocomissao',
            index=models.Index(fields=['token_vendedor'], name='rc_token_vendedor_idx'),
        ),
        migrations.AddIndex(
            model_name='relatoriocomissao',
            index=models.Index(fields=['asaas_payment_id'], name='rc_asaas_pay_idx'),
        ),
    ]
