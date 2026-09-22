"""to_decimal recusa NaN e infinito."""
from decimal import Decimal

from django.test import SimpleTestCase

from core.decimal_utils import to_decimal


class ToDecimalFinitoTest(SimpleTestCase):
    def test_numero_normal(self):
        self.assertEqual(to_decimal("10.50"), Decimal("10.50"))

    def test_nan_e_infinito_sao_invalidos(self):
        for bruto in ("NaN", "Infinity", "-Infinity", "inf", "-inf"):
            with self.assertRaises(ValueError):
                to_decimal(bruto, "amount")
