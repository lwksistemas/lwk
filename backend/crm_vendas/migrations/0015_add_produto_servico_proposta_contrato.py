# ProdutoServico, OportunidadeItem, Proposta, Contrato

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0014_add_criado_por_vendedor_id_to_atividade'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProdutoServico',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.IntegerField(db_index=True, help_text='ID da loja proprietária deste registro')),
                ('tipo', models.CharField(choices=[('produto', 'Produto'), ('servico', 'Serviço')], default='produto', max_length=20)),
                ('nome', models.CharField(max_length=255)),
                ('descricao', models.TextField(blank=True)),
                ('preco', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('ativo', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Produto/Serviço',
                'verbose_name_plural': 'Produtos e Serviços',
                'db_table': 'crm_vendas_produto_servico',
                'ordering': ['tipo', 'nome'],
            },
        ),
        migrations.CreateModel(
            name='Proposta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.IntegerField(db_index=True, help_text='ID da loja proprietária deste registro')),
                ('titulo', models.CharField(max_length=255)),
                ('conteudo', models.TextField(blank=True, help_text='Conteúdo da proposta em texto ou HTML')),
                ('valor_total', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('status', models.CharField(choices=[('rascunho', 'Rascunho'), ('enviada', 'Enviada'), ('aceita', 'Aceita'), ('rejeitada', 'Rejeitada')], default='rascunho', max_length=20)),
                ('data_envio', models.DateTimeField(blank=True, null=True)),
                ('data_resposta', models.DateTimeField(blank=True, null=True)),
                ('observacoes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('oportunidade', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='propostas', to='crm_vendas.oportunidade')),
            ],
            options={
                'verbose_name': 'Proposta',
                'verbose_name_plural': 'Propostas',
                'db_table': 'crm_vendas_proposta',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Contrato',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.IntegerField(db_index=True, help_text='ID da loja proprietária deste registro')),
                ('numero', models.CharField(blank=True, max_length=50)),
                ('titulo', models.CharField(max_length=255)),
                ('conteudo', models.TextField(blank=True, help_text='Conteúdo do contrato')),
                ('valor_total', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('status', models.CharField(choices=[('rascunho', 'Rascunho'), ('enviado', 'Enviado'), ('assinado', 'Assinado'), ('cancelado', 'Cancelado')], default='rascunho', max_length=20)),
                ('data_envio', models.DateTimeField(blank=True, null=True)),
                ('data_assinatura', models.DateTimeField(blank=True, null=True)),
                ('observacoes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('oportunidade', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='contrato', to='crm_vendas.oportunidade')),
            ],
            options={
                'verbose_name': 'Contrato',
                'verbose_name_plural': 'Contratos',
                'db_table': 'crm_vendas_contrato',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OportunidadeItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.IntegerField(db_index=True, help_text='ID da loja proprietária deste registro')),
                ('quantidade', models.DecimalField(decimal_places=2, default=1, max_digits=10)),
                ('preco_unitario', models.DecimalField(decimal_places=2, max_digits=12)),
                ('observacao', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('oportunidade', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='itens', to='crm_vendas.oportunidade')),
                ('produto_servico', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='oportunidade_itens', to='crm_vendas.produtoservico')),
            ],
            options={
                'verbose_name': 'Item da Oportunidade',
                'verbose_name_plural': 'Itens da Oportunidade',
                'db_table': 'crm_vendas_oportunidade_item',
                'ordering': ['id'],
            },
        ),
        migrations.AddIndex(
            model_name='produtoservico',
            index=models.Index(fields=['loja_id', 'tipo'], name='crm_ps_loja_tipo_idx'),
        ),
        migrations.AddIndex(
            model_name='produtoservico',
            index=models.Index(fields=['loja_id', 'ativo'], name='crm_ps_loja_ativo_idx'),
        ),
        migrations.AddIndex(
            model_name='proposta',
            index=models.Index(fields=['loja_id', 'oportunidade'], name='crm_prop_loja_opor_idx'),
        ),
        migrations.AddIndex(
            model_name='proposta',
            index=models.Index(fields=['loja_id', 'status'], name='crm_prop_loja_status_idx'),
        ),
        migrations.AddIndex(
            model_name='contrato',
            index=models.Index(fields=['loja_id', 'oportunidade'], name='crm_cont_loja_opor_idx'),
        ),
        migrations.AddIndex(
            model_name='contrato',
            index=models.Index(fields=['loja_id', 'status'], name='crm_cont_loja_status_idx'),
        ),
        migrations.AddIndex(
            model_name='oportunidadeitem',
            index=models.Index(fields=['loja_id', 'oportunidade'], name='crm_oi_loja_opor_idx'),
        ),
    ]
