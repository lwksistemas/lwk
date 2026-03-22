# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0028_vendedor_comissao_padrao'),
    ]

    operations = [
        # Criar tabela CategoriaProdutoServico
        migrations.CreateModel(
            name='CategoriaProdutoServico',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.IntegerField(db_index=True, help_text='ID da loja (isolamento multi-tenant)')),
                ('nome', models.CharField(help_text='Nome da categoria (ex: Hardware, Software, Consultoria)', max_length=100)),
                ('descricao', models.TextField(blank=True, help_text='Descrição da categoria')),
                ('cor', models.CharField(default='#3B82F6', help_text='Cor para identificação visual (hex)', max_length=7)),
                ('ordem', models.IntegerField(default=0, help_text='Ordem de exibição')),
                ('ativo', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Categoria de Produto/Serviço',
                'verbose_name_plural': 'Categorias de Produtos/Serviços',
                'db_table': 'crm_vendas_categoria_produto_servico',
                'ordering': ['ordem', 'nome'],
            },
        ),
        
        # Adicionar índices para CategoriaProdutoServico
        migrations.AddIndex(
            model_name='categoriaprodutoservico',
            index=models.Index(fields=['loja_id', 'ativo'], name='crm_cat_ps_loja_ativo_idx'),
        ),
        migrations.AddIndex(
            model_name='categoriaprodutoservico',
            index=models.Index(fields=['loja_id', 'ordem'], name='crm_cat_ps_loja_ordem_idx'),
        ),
        
        # Adicionar campo codigo em ProdutoServico
        migrations.AddField(
            model_name='produtoservico',
            name='codigo',
            field=models.CharField(blank=True, help_text='Código interno único (ex: PROD-001, SERV-CONS-01)', max_length=50),
        ),
        
        # Adicionar campo categoria em ProdutoServico
        migrations.AddField(
            model_name='produtoservico',
            name='categoria',
            field=models.ForeignKey(
                blank=True,
                help_text='Categoria/Grupo do produto ou serviço',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='produtos_servicos',
                to='crm_vendas.categoriaprodutoservico'
            ),
        ),
        
        # Adicionar índices para os novos campos
        migrations.AddIndex(
            model_name='produtoservico',
            index=models.Index(fields=['loja_id', 'categoria'], name='crm_ps_loja_cat_idx'),
        ),
        migrations.AddIndex(
            model_name='produtoservico',
            index=models.Index(fields=['loja_id', 'codigo'], name='crm_ps_loja_codigo_idx'),
        ),
        
        # Adicionar constraint de unicidade para código dentro da loja
        migrations.AddConstraint(
            model_name='produtoservico',
            constraint=models.UniqueConstraint(
                condition=models.Q(('codigo__isnull', False), ('codigo', ''), _negated=True),
                fields=('loja_id', 'codigo'),
                name='crm_ps_unique_codigo_loja'
            ),
        ),
        
        # Atualizar ordering de ProdutoServico
        migrations.AlterModelOptions(
            name='produtoservico',
            options={
                'ordering': ['categoria__ordem', 'categoria__nome', 'codigo', 'nome'],
                'verbose_name': 'Produto/Serviço',
                'verbose_name_plural': 'Produtos e Serviços'
            },
        ),
    ]
