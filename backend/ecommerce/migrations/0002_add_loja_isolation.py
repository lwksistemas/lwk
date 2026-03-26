# Generated migration for adding LojaIsolationMixin to ecommerce models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0001_initial'),
    ]

    operations = [
        # Add loja_id to all models
        migrations.AddField(
            model_name='categoria',
            name='loja_id',
            field=models.IntegerField(db_index=True, default=1, help_text='ID da loja (isolamento multi-tenant)'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='produto',
            name='loja_id',
            field=models.IntegerField(db_index=True, default=1, help_text='ID da loja (isolamento multi-tenant)'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='cliente',
            name='loja_id',
            field=models.IntegerField(db_index=True, default=1, help_text='ID da loja (isolamento multi-tenant)'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='pedido',
            name='loja_id',
            field=models.IntegerField(db_index=True, default=1, help_text='ID da loja (isolamento multi-tenant)'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='cupom',
            name='loja_id',
            field=models.IntegerField(db_index=True, default=1, help_text='ID da loja (isolamento multi-tenant)'),
            preserve_default=False,
        ),
        
        # Remove unique constraint from Produto.sku (will be replaced with loja_id + sku)
        migrations.AlterField(
            model_name='produto',
            name='sku',
            field=models.CharField(max_length=50),
        ),
        
        # Remove unique constraint from Cupom.codigo (will be replaced with loja_id + codigo)
        migrations.AlterField(
            model_name='cupom',
            name='codigo',
            field=models.CharField(max_length=50),
        ),
        
        # Add unique constraints with loja_id
        migrations.AddConstraint(
            model_name='produto',
            constraint=models.UniqueConstraint(
                fields=['loja_id', 'sku'],
                name='ecommerce_produto_sku_loja_uniq'
            ),
        ),
        migrations.AddConstraint(
            model_name='cupom',
            constraint=models.UniqueConstraint(
                fields=['loja_id', 'codigo'],
                name='ecommerce_cupom_codigo_loja_uniq'
            ),
        ),
    ]
