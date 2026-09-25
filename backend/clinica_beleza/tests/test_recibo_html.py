"""Cupom HTML do recibo usa o mesmo contexto do PDF."""
from django.test import SimpleTestCase

from clinica_beleza.recibo.html import gerar_html_recibo


class GerarHtmlReciboTests(SimpleTestCase):
    def _ctx(self, **overrides):
        base = {
            "loja_nome": "HARMONIS",
            "loja_cnpj": "37302743000126",
            "loja_endereco": "Rua A, 1",
            "loja_telefone": "1633330000",
            "loja_email": "a@b.com",
            "loja_cep": "14000000",
            "paciente_nome": "Maria Silva",
            "profissional_nome": "Dra. Ana",
            "data_emissao": "20/09/2026 15:00",
            "data": "20/09/2026 14:00",
            "data_atendimento": "20/09/2026 14:00",
            "procedimentos": [{"nome": "CRIOGENIA", "valor": 200.0}],
            "taxa_consulta": 150.0,
            "desconto": 0.0,
            "desconto_retorno": 0.0,
            "retorno_gratuito": False,
            "subtotal": 350.0,
            "valor_total": 350.0,
            "valor_pago": 350.0,
            "saldo_devedor": 0.0,
            "vencimento": "",
            "metodo": "Dinheiro",
            "formas_pagamento": [{"metodo": "Dinheiro (20/09/2026)", "valor": 350.0}],
            "retorno_aviso": "",
        }
        base.update(overrides)
        return base

    def test_mostra_desconto_retorno_sem_prazo(self):
        html = gerar_html_recibo(
            self._ctx(
                retorno_gratuito=True,
                taxa_consulta=0.0,
                taxa_consulta_referencia=150.0,
                desconto_retorno=150.0,
                subtotal=350.0,
                valor_total=200.0,
                valor_pago=200.0,
            ),
        )
        self.assertIn("Desconto retorno", html)
        self.assertNotIn("prazo", html)

    def test_escapa_html_do_nome(self):
        html = gerar_html_recibo(self._ctx(paciente_nome="<img src=x>"))
        self.assertIn("&lt;img src=x&gt;", html)
        self.assertNotIn("<img src=x>", html)

    def test_retorno_sem_valor_lista_procedimento_e_isento(self):
        html = gerar_html_recibo(
            self._ctx(
                retorno_gratuito=True,
                taxa_consulta=0.0,
                taxa_consulta_referencia=150.0,
                desconto_retorno=150.0,
                desconto=0.0,
                procedimentos=[{"nome": "LASER ETHEREA", "valor": 0.0}],
                subtotal=150.0,
                valor_total=0.0,
                valor_pago=0.0,
                saldo_devedor=0.0,
                formas_pagamento=[],
                metodo="",
            ),
        )
        self.assertIn("RECIBO DE RETORNO", html)
        self.assertIn("LASER ETHEREA", html)
        self.assertIn("Isento — retorno", html)
        self.assertIn("Retorno isento", html)
        self.assertIn("Desconto retorno", html)
        self.assertNotIn(">Desconto<", html)

    def test_quitado_quando_sem_saldo(self):
        html = gerar_html_recibo(self._ctx())
        self.assertIn("Quitado", html)
        self.assertIn("RECIBO DE PAGAMENTO", html)
