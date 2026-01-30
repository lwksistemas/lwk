# Generated manually - isolamento por loja (Categoria, ItemCardapio, Mesa, Cliente, Reserva, Pedido)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurante', '0007_add_registro_peso_balanca'),
    ]

    operations = [
        # Categoria
        migrations.AddField(
            model_name='categoria',
            name='loja_id',
            field=models.IntegerField(db_index=True, default=1, help_text='ID da loja proprietária deste registro'),
            preserve_default=False,
        ),
        # ItemCardapio
        migrations.AddField(
            model_name='itemcardapio',
            name='loja_id',
            field=models.IntegerField(db_index=True, default=1, help_text='ID da loja proprietária deste registro'),
            preserve_default=False,
        ),
        # Mesa: remover unique do numero e adicionar loja_id
        migrations.AlterField(
            model_name='mesa',
            name='numero',
            field=models.CharField(max_length=10),
        ),
        migrations.AddField(
            model_name='mesa',
            name='loja_id',
            field=models.IntegerField(db_index=True, default=1, help_text='ID da loja proprietária deste registro'),
            preserve_default=False,
        ),
        migrations.AddConstraint(
            model_name='mesa',
            constraint=models.UniqueConstraint(fields=('loja_id', 'numero'), name='restaurante_mesa_numero_loja_uniq'),
        ),
        # Cliente
        migrations.AddField(
            model_name='cliente',
            name='loja_id',
            field=models.IntegerField(db_index=True, default=1, help_text='ID da loja proprietária deste registro'),
            preserve_default=False,
        ),
        # Reserva
        migrations.AddField(
            model_name='reserva',
            name='loja_id',
            field=models.IntegerField(db_index=True, default=1, help_text='ID da loja proprietária deste registro'),
            preserve_default=False,
        ),
        # Pedido
        migrations.AddField(
            model_name='pedido',
            name='loja_id',
            field=models.IntegerField(db_index=True, default=1, help_text='ID da loja proprietária deste registro'),
            preserve_default=False,
        ),
    ]
