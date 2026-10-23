"""A pasta da prestadora soma os itens das subpastas sem listar cada serviço."""
from django.test import SimpleTestCase


class SomarTotaisPastasTests(SimpleTestCase):
    def test_raiz_recebe_a_soma_das_subpastas(self):
        from crm_vendas.views import somar_totais_pastas

        totais = somar_totais_pastas(
            {2: 400, 3: 189},
            {1: None, 2: 1, 3: 1},
        )
        self.assertEqual(totais[1], 589)
        self.assertEqual(totais[2], 400)
        self.assertEqual(totais[3], 189)
