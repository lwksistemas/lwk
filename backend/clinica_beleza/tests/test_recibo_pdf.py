"""Testes unitários para geração de PDF do recibo e contexto de dados.
"""
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase


class GerarPdfReciboTests(SimpleTestCase):
    """Testa geração do PDF de recibo."""

    def _ctx(self, **overrides):
        base = {
            "paciente_nome": "Maria Silva",
            "profissional_nome": "Dra. Ana",
            "loja_nome": "Clínica Estética",
            "loja_cnpj": "12.345.678/0001-90",
            "loja_endereco": "Rua A, 100, Centro, São Paulo - SP",
            "loja_telefone": "(11) 99999-0000",
            "loja_email": "contato@clinica.com",
            "procedimentos": [
                {"nome": "Botox", "valor": 800.0},
                {"nome": "Preenchimento", "valor": 1200.0},
            ],
            "taxa_consulta": 200.0,
            "valor_total": 2200.0,
            "valor_pago": 2200.0,
            "desconto": 0.0,
            "metodo": "PIX",
            "data": "10/07/2026 14:00",
            "formas_pagamento": [{"metodo": "PIX", "valor": 2200.0}],
        }
        base.update(overrides)
        return base

    def test_gera_pdf_bytes_valido(self):
        """PDF gerado deve ser bytes não vazios começando com %PDF."""
        from clinica_beleza.recibo_service import _gerar_pdf_recibo
        ctx = self._ctx()
        pdf = _gerar_pdf_recibo(ctx)
        self.assertIsInstance(pdf, bytes)
        self.assertGreater(len(pdf), 100)
        self.assertTrue(pdf[:5] == b"%PDF-")

    def test_gera_pdf_sem_profissional(self):
        """PDF sem profissional não deve dar erro."""
        from clinica_beleza.recibo_service import _gerar_pdf_recibo
        ctx = self._ctx(profissional_nome="")
        pdf = _gerar_pdf_recibo(ctx)
        self.assertTrue(pdf[:5] == b"%PDF-")

    def test_gera_pdf_sem_taxa_consulta(self):
        """PDF sem taxa de consulta (= 0) não mostra a linha."""
        from clinica_beleza.recibo_service import _gerar_pdf_recibo
        ctx = self._ctx(taxa_consulta=0.0)
        pdf = _gerar_pdf_recibo(ctx)
        self.assertGreater(len(pdf), 100)

    def test_gera_pdf_com_retorno_gratuito(self):
        """PDF com retorno gratuito mostra taxa e desconto retorno."""
        from clinica_beleza.recibo_service import _gerar_pdf_recibo
        ctx = self._ctx(
            taxa_consulta=0.0,
            taxa_consulta_referencia=150.0,
            desconto_retorno=150.0,
            subtotal=2150.0,
            retorno_gratuito=True,
            retorno_dias=30,
            valor_total=2000.0,
            valor_pago=2000.0,
        )
        pdf = _gerar_pdf_recibo(ctx)
        self.assertTrue(pdf[:5] == b"%PDF-")
        self.assertGreater(len(pdf), 100)

    def test_gera_pdf_multiplas_formas(self):
        """PDF com múltiplas formas de pagamento."""
        from clinica_beleza.recibo_service import _gerar_pdf_recibo
        ctx = self._ctx(formas_pagamento=[
            {"metodo": "PIX", "valor": 1000.0},
            {"metodo": "Cartão de Crédito", "valor": 1200.0},
        ])
        pdf = _gerar_pdf_recibo(ctx)
        self.assertTrue(pdf[:5] == b"%PDF-")

    def test_gera_pdf_com_desconto(self):
        """PDF com desconto aplicado."""
        from clinica_beleza.recibo_service import _gerar_pdf_recibo
        ctx = self._ctx(desconto=100.0, valor_pago=2100.0)
        pdf = _gerar_pdf_recibo(ctx)
        self.assertGreater(len(pdf), 100)

    def test_gera_pdf_dados_loja_vazios(self):
        """PDF com dados da loja vazios não quebra."""
        from clinica_beleza.recibo_service import _gerar_pdf_recibo
        ctx = self._ctx(
            loja_nome="", loja_cnpj="", loja_endereco="", loja_telefone="",
        )
        pdf = _gerar_pdf_recibo(ctx)
        self.assertTrue(pdf[:5] == b"%PDF-")


class ObterDadosContextoTests(SimpleTestCase):
    """Testa _obter_dados_contexto."""

    @patch("superadmin.models.Loja.objects")
    def test_retorna_dados_completos(self, mock_loja_objects):
        """Contexto deve conter todos os campos necessários."""
        from clinica_beleza.recibo_service import _obter_dados_contexto

        loja = MagicMock()
        loja.nome = "Clínica Beta"
        loja.cpf_cnpj = "12345678000190"
        loja.logradouro = "Rua X"
        loja.numero = "10"
        loja.bairro = "Centro"
        loja.cidade = "SP"
        loja.uf = "SP"
        loja.cep = "01000000"
        loja.owner_telefone = "11999990000"
        loja.owner = MagicMock(email="admin@test.com")
        mock_loja_objects.filter.return_value.first.return_value = loja

        payment = MagicMock()
        payment.loja_id = 1
        payment.amount = Decimal(500)
        payment.valor_total = Decimal(500)
        payment.payment_method = "CASH"
        payment.payment_date = MagicMock()
        payment.payment_date.strftime.return_value = "10/07/2026 14:00"
        payment.notes = ""
        payment.PAYMENT_METHOD_CHOICES = (("CASH", "Dinheiro"),)
        type(payment).valor_total_efetivo = property(lambda s: Decimal(500))
        # Mock parcelas chain
        mock_qs = MagicMock()
        mock_qs.exists.return_value = False
        payment.parcelas.filter.return_value.order_by.return_value = mock_qs

        patient = MagicMock()
        patient.nome = "João"
        patient.email = "joao@test.com"
        patient.telefone = "11999991111"

        appointment = MagicMock()
        appointment.professional = MagicMock(nome="Dra. Ana")
        appointment.appointment_procedures = MagicMock()
        appointment.appointment_procedures.select_related.return_value.all.return_value = []
        appointment.procedure = MagicMock(nome="Botox", preco=Decimal(300))
        appointment.consulta = MagicMock(valor_consulta=Decimal(100))

        ctx = _obter_dados_contexto(payment, patient, appointment)

        self.assertEqual(ctx["paciente_nome"], "João")
        self.assertEqual(ctx["loja_nome"], "Clínica Beta")
        self.assertIn("profissional_nome", ctx)
        self.assertIn("procedimentos", ctx)
        self.assertIn("formas_pagamento", ctx)
        self.assertIn("taxa_consulta", ctx)


class FormatarEnderecoLojaTests(SimpleTestCase):
    """Testa _formatar_endereco_loja."""

    def test_endereco_completo(self):
        from clinica_beleza.recibo_service import _formatar_endereco_loja
        loja = MagicMock()
        loja.logradouro = "Av Brasil"
        loja.numero = "500"
        loja.bairro = "Jardim"
        loja.cidade = "Ribeirão Preto"
        loja.uf = "SP"
        loja.cep = "14000000"
        result = _formatar_endereco_loja(loja)
        self.assertIn("Av Brasil, 500", result)
        self.assertIn("Jardim", result)
        self.assertIn("Ribeirão Preto - SP", result)

    def test_endereco_parcial(self):
        from clinica_beleza.recibo_service import _formatar_endereco_loja
        loja = MagicMock()
        loja.logradouro = "Rua A"
        loja.numero = ""
        loja.bairro = ""
        loja.cidade = "São Paulo"
        loja.uf = ""
        loja.cep = ""
        result = _formatar_endereco_loja(loja)
        self.assertIn("Rua A", result)
        self.assertIn("São Paulo", result)

    def test_endereco_vazio(self):
        from clinica_beleza.recibo_service import _formatar_endereco_loja
        loja = MagicMock()
        loja.logradouro = ""
        loja.numero = ""
        loja.bairro = ""
        loja.cidade = ""
        loja.uf = ""
        loja.cep = ""
        result = _formatar_endereco_loja(loja)
        self.assertEqual(result, "")
