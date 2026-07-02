"""Validações de envio de documento e view financeiro PDF."""
from io import BytesIO
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from crm_vendas.views_enviar_cliente import _validar_envio_documento_cliente
from crm_vendas.views_financeiro import financeiro_crm_relatorio_pdf


def _doc(*, email='a@b.com', telefone='11999999999', lead_id=1):
    lead = MagicMock()
    lead.email = email
    lead.telefone = telefone
    doc = MagicMock()
    doc.oportunidade = MagicMock()
    doc.oportunidade.lead_id = lead_id
    doc.oportunidade.lead = lead
    return doc


class ValidarEnvioDocumentoClienteTest(SimpleTestCase):
    def test_sem_oportunidade(self):
        doc = MagicMock()
        doc.oportunidade = None
        self.assertIn('oportunidade', (_validar_envio_documento_cliente(doc, 'email') or '').lower())

    def test_email_sem_endereco(self):
        err = _validar_envio_documento_cliente(_doc(email='  '), 'email')
        self.assertIn('e-mail', (err or '').lower())

    def test_whatsapp_sem_telefone(self):
        err = _validar_envio_documento_cliente(_doc(telefone=''), 'whatsapp')
        self.assertIn('telefone', (err or '').lower())

    def test_canal_invalido(self):
        err = _validar_envio_documento_cliente(_doc(), 'sms')
        self.assertIn('canal', (err or '').lower())

    def test_email_valido(self):
        self.assertIsNone(_validar_envio_documento_cliente(_doc(), 'email'))

    def test_whatsapp_valido(self):
        self.assertIsNone(_validar_envio_documento_cliente(_doc(), 'whatsapp'))


class FinanceiroCrmRelatorioPdfViewTest(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    @patch('tenants.middleware.get_current_loja_id', return_value=None)
    @patch('crm_vendas.views_financeiro.get_current_loja_id', return_value=None)
    def test_sem_loja_retorna_400(self, _view_loja, _mw_loja):
        request = self.factory.post('/api/crm-vendas/financeiro/relatorio-pdf/', {}, format='json')
        force_authenticate(request, user=MagicMock())
        response = financeiro_crm_relatorio_pdf(request)
        self.assertEqual(response.status_code, 400)

    @patch('crm_vendas.views_financeiro.get_current_loja_id', return_value=4)
    def test_periodo_personalizado_sem_datas_400(self, _loja):
        request = self.factory.post(
            '/api/crm-vendas/financeiro/relatorio-pdf/',
            {'periodo': 'personalizado'},
            format='json',
        )
        force_authenticate(request, user=MagicMock())
        response = financeiro_crm_relatorio_pdf(request)
        self.assertEqual(response.status_code, 400)

    @patch('crm_vendas.relatorios_financeiro.gerar_relatorio_financeiro_vendedor')
    @patch('crm_vendas.views_financeiro.is_owner', return_value=True)
    @patch('crm_vendas.views_financeiro.get_current_vendedor_id', return_value=None)
    @patch('crm_vendas.views_financeiro.get_current_loja_id', return_value=4)
    def test_gera_pdf_com_sucesso(self, _loja, _vend, _owner, mock_gerar):
        buf = BytesIO(b'%PDF-fake')
        mock_gerar.return_value = buf
        request = self.factory.post(
            '/api/crm-vendas/financeiro/relatorio-pdf/',
            {'periodo': 'mes_atual'},
            format='json',
        )
        force_authenticate(request, user=MagicMock())
        response = financeiro_crm_relatorio_pdf(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
