"""
Testes do app restaurante: serializers e ViewSets (isolamento por loja).
"""
from decimal import Decimal
from django.test import TestCase
from core.mixins import set_loja_context, clear_loja_context
from .models import Categoria, ItemCardapio, Mesa
from .serializers import (
    CategoriaSerializer, ItemCardapioSerializer, MesaSerializer,
)


class CategoriaSerializerTest(TestCase):
    """Validação do CategoriaSerializer."""

    def setUp(self):
        set_loja_context(1)

    def tearDown(self):
        clear_loja_context()

    def test_categoria_valid(self):
        data = {'nome': 'Bebidas', 'descricao': 'Refrigerantes e sucos', 'ordem': 1, 'loja_id': 1}
        ser = CategoriaSerializer(data=data)
        self.assertTrue(ser.is_valid(), ser.errors)
        cat = ser.save()
        self.assertEqual(cat.nome, 'Bebidas')
        self.assertEqual(cat.loja_id, 1)

    def test_categoria_missing_nome(self):
        data = {'descricao': 'Teste', 'ordem': 0, 'loja_id': 1}
        ser = CategoriaSerializer(data=data)
        self.assertFalse(ser.is_valid())
        self.assertIn('nome', ser.errors)


class ItemCardapioSerializerTest(TestCase):
    """Validação do ItemCardapioSerializer."""

    def setUp(self):
        set_loja_context(1)
        self.categoria = Categoria.objects.create(
            nome='Bebidas', descricao='', ordem=0, loja_id=1
        )

    def tearDown(self):
        clear_loja_context()

    def test_item_cardapio_valid(self):
        data = {
            'nome': 'Refrigerante',
            'descricao': 'Lata 350ml',
            'categoria': self.categoria.id,
            'preco': '5.50',
            'tempo_preparo': 5,
            'is_disponivel': True,
            'loja_id': 1,
        }
        ser = ItemCardapioSerializer(data=data)
        self.assertTrue(ser.is_valid(), ser.errors)
        item = ser.save()
        self.assertEqual(item.nome, 'Refrigerante')
        self.assertEqual(item.preco, Decimal('5.50'))
        self.assertEqual(item.loja_id, 1)

    def test_item_cardapio_invalid_preco_empty(self):
        data = {
            'nome': 'Item',
            'descricao': 'Desc',
            'categoria': self.categoria.id,
            'preco': '',
            'tempo_preparo': 10,
            'loja_id': 1,
        }
        ser = ItemCardapioSerializer(data=data)
        self.assertFalse(ser.is_valid())
        self.assertIn('preco', ser.errors)

    def test_item_cardapio_missing_required(self):
        data = {'nome': 'Só nome', 'loja_id': 1}
        ser = ItemCardapioSerializer(data=data)
        self.assertFalse(ser.is_valid())
        self.assertIn('descricao', ser.errors)


class MesaSerializerTest(TestCase):
    """Validação do MesaSerializer."""

    def setUp(self):
        set_loja_context(1)

    def tearDown(self):
        clear_loja_context()

    def test_mesa_valid(self):
        data = {
            'numero': '01',
            'capacidade': 4,
            'status': 'livre',
            'is_active': True,
            'loja_id': 1,
        }
        ser = MesaSerializer(data=data)
        self.assertTrue(ser.is_valid(), ser.errors)
        mesa = ser.save()
        self.assertEqual(mesa.numero, '01')
        self.assertEqual(mesa.loja_id, 1)


class LojaIsolationManagerTest(TestCase):
    """LojaIsolationManager filtra querysets por loja_id do contexto."""

    def setUp(self):
        set_loja_context(1)
        self.cat = Categoria.objects.create(
            nome='Cat Loja 1', descricao='', ordem=0, loja_id=1
        )
        ItemCardapio.objects.create(
            nome='Item Loja 1',
            descricao='Desc',
            categoria=self.cat,
            preco=Decimal('10.00'),
            tempo_preparo=10,
            loja_id=1,
        )
        Mesa.objects.create(numero='1', capacidade=4, loja_id=1)

    def tearDown(self):
        clear_loja_context()

    def test_categoria_queryset_filtered(self):
        set_loja_context(1)
        qs = Categoria.objects.all()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().nome, 'Cat Loja 1')

    def test_cardapio_queryset_filtered(self):
        set_loja_context(1)
        qs = ItemCardapio.objects.all()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().nome, 'Item Loja 1')

    def test_empty_queryset_when_no_loja_context(self):
        clear_loja_context()
        self.assertEqual(Categoria.objects.all().count(), 0)
        self.assertEqual(ItemCardapio.objects.all().count(), 0)
