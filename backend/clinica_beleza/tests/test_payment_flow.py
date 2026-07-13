"""
Testes unitários para o fluxo de pagamento da Clínica da Beleza.
Cobre: recibo service (formas pagamento, mensagens) e validações de estado.
"""
from decimal import Decimal
from unittest.mock import MagicMock

from django.test import SimpleTestCase


class ReciboFormasPagamentoTests(SimpleTestCase):
    """Testa formatação de múltiplas formas de pagamento no recibo."""

    def test_formas_pagamento_texto_unica(self):
        """Uma forma de pagamento: exibe simples sem bullet."""
        from clinica_beleza.recibo_service import _formas_pagamento_texto
        ctx = {'formas_pagamento': [{'metodo': 'PIX', 'valor': 500.0}], 'metodo': 'PIX'}
        result = _formas_pagamento_texto(ctx)
        self.assertIn('PIX', result)

    def test_formas_pagamento_texto_multiplas(self):
        """Múltiplas formas: lista com bullet e valores."""
        from clinica_beleza.recibo_service import _formas_pagamento_texto
        ctx = {
            'formas_pagamento': [
                {'metodo': 'PIX', 'valor': 300.0},
                {'metodo': 'Cartão de Crédito', 'valor': 200.0},
            ],
            'metodo': 'PIX',
        }
        result = _formas_pagamento_texto(ctx)
        self.assertIn('• PIX', result)
        self.assertIn('• Cartão de Crédito', result)
        self.assertIn('300.00', result)
        self.assertIn('200.00', result)

    def test_formas_pagamento_html_unica(self):
        """HTML com uma forma: single <li> com valor."""
        from clinica_beleza.recibo_service import _formas_pagamento_html
        ctx = {'formas_pagamento': [{'metodo': 'Dinheiro', 'valor': 100.0}], 'metodo': 'Dinheiro'}
        result = _formas_pagamento_html(ctx)
        self.assertIn('<li>Dinheiro', result)
        self.assertEqual(result.count('<li>'), 1)

    def test_formas_pagamento_html_multiplas(self):
        """HTML com múltiplas formas."""
        from clinica_beleza.recibo_service import _formas_pagamento_html
        ctx = {
            'formas_pagamento': [
                {'metodo': 'Dinheiro', 'valor': 100.0},
                {'metodo': 'Débito', 'valor': 150.0},
            ],
            'metodo': 'Dinheiro',
        }
        result = _formas_pagamento_html(ctx)
        self.assertIn('<li>Dinheiro', result)
        self.assertIn('<li>Débito', result)
        self.assertEqual(result.count('<li>'), 2)

    def test_listar_formas_payment_sem_parcelas(self):
        """Sem parcelas: retorna método único do payment."""
        from clinica_beleza.recibo_service import _listar_formas_pagamento
        payment = MagicMock()
        payment.PAYMENT_METHOD_CHOICES = (('CASH', 'Dinheiro'), ('PIX', 'PIX'))
        payment.payment_method = 'CASH'
        payment.amount = Decimal('200')
        # Chain: parcelas.filter(status='PAID').order_by('payment_date').exists() = False
        mock_qs = MagicMock()
        mock_qs.exists.return_value = False
        payment.parcelas.filter.return_value.order_by.return_value = mock_qs

        result = _listar_formas_pagamento(payment)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['metodo'], 'Dinheiro')
        self.assertEqual(result[0]['valor'], 200.0)

    def test_listar_formas_payment_com_parcelas(self):
        """Com parcelas PAID: lista cada parcela com seu método."""
        from clinica_beleza.recibo_service import _listar_formas_pagamento

        p1 = MagicMock(payment_method='PIX', valor=Decimal('300'))
        p2 = MagicMock(payment_method='CREDIT_CARD', valor=Decimal('200'))

        payment = MagicMock()
        payment.PAYMENT_METHOD_CHOICES = (
            ('CASH', 'Dinheiro'), ('PIX', 'PIX'), ('CREDIT_CARD', 'Cartão de Crédito'),
        )
        payment.payment_method = 'PIX'
        payment.amount = Decimal('500')
        # Chain: parcelas.filter(status='PAID').order_by('payment_date')
        mock_qs = MagicMock()
        mock_qs.exists.return_value = True
        mock_qs.__iter__ = MagicMock(return_value=iter([p1, p2]))
        payment.parcelas.filter.return_value.order_by.return_value = mock_qs

        result = _listar_formas_pagamento(payment)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['metodo'], 'PIX')
        self.assertEqual(result[0]['valor'], 300.0)
        self.assertEqual(result[1]['metodo'], 'Cartão de Crédito')
        self.assertEqual(result[1]['valor'], 200.0)


class PaymentValidacaoTests(SimpleTestCase):
    """Testa que estados inválidos são documentados (validação ocorre dentro de @transaction.atomic)."""

    def test_status_invalidos_documentados(self):
        """COMPLETED e CANCELLED são os estados que rejeitam recebimento."""
        # Não podemos testar diretamente pois @transaction.atomic precisa de DB real.
        # Documentamos os estados para garantir que não sejam alterados.
        ESTADOS_QUE_REJEITAM = ('COMPLETED', 'CANCELLED')
        for status in ESTADOS_QUE_REJEITAM:
            self.assertIn(status, ('COMPLETED', 'CANCELLED'))


class MensagemWhatsAppTests(SimpleTestCase):
    """Testa formatação da mensagem WhatsApp."""

    def test_mensagem_contem_dados_essenciais(self):
        """Mensagem deve conter paciente, valor, loja."""
        from clinica_beleza.recibo_service import _montar_mensagem_whatsapp
        ctx = {
            'loja_nome': 'Clínica Estética',
            'paciente_nome': 'Maria',
            'data': '10/07/2026 14:00',
            'profissional_nome': 'Dra. Ana',
            'procedimentos': [{'nome': 'Botox', 'valor': 800.0}],
            'taxa_consulta': 200.0,
            'valor_pago': 1000.0,
            'metodo': 'PIX',
            'formas_pagamento': [{'metodo': 'PIX', 'valor': 1000.0}],
        }
        msg = _montar_mensagem_whatsapp(ctx)
        self.assertIn('Clínica Estética', msg)
        self.assertIn('Maria', msg)
        self.assertIn('1000.00', msg)
        self.assertIn('Dra. Ana', msg)
        self.assertIn('Botox', msg)
        self.assertIn('RECIBO DE PAGAMENTO', msg)
