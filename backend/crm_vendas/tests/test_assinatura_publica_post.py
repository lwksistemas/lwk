"""Teste de integração leve: POST público de assinatura não quebra por ImportError."""
import json
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, SimpleTestCase

from crm_vendas.views_assinatura_publica import AssinaturaPublicaView


class TestAssinaturaPublicaPost(SimpleTestCase):
  def setUp(self):
    self.factory = RequestFactory()
    self.token = 'signed-token-mock'
    self.loja_id = 42

  def _post(self):
    request = self.factory.post(
      f'/api/crm-vendas/assinar/{self.token}/',
      data=json.dumps({}),
      content_type='application/json',
    )
    return AssinaturaPublicaView.as_view()(request, token=self.token)

  @patch('crm_vendas.assinatura_publica_helpers.cache')
  @patch('crm_vendas.views_assinatura_publica.configurar_tenant_para_assinatura_publica', return_value=None)
  @patch('crm_vendas.assinatura_digital_service.notificar_vendedor_apos_assinatura_cliente', return_value=(True, None))
  @patch('crm_vendas.assinatura_digital_service.registrar_assinatura', return_value='aguardando_vendedor')
  @patch('crm_vendas.assinatura_digital_service.verificar_token_assinatura')
  @patch('crm_vendas.assinatura_digital_service.normalizar_token_assinatura_url', side_effect=lambda t: t)
  @patch('crm_vendas.assinatura_publica_helpers.loads')
  def test_post_cliente_assina_retorna_sucesso(
    self,
    mock_loads,
    _norm,
    mock_verificar,
    mock_registrar,
    _notificar,
    _cfg,
    mock_cache,
  ):
    mock_cache.get.return_value = 0
    mock_loads.return_value = {'loja_id': self.loja_id}
    assinatura = MagicMock()
    documento = MagicMock(__class__=type('Proposta', (), {}))
    documento.get_status_assinatura_display.return_value = 'Aguardando vendedor'
    assinatura.documento = documento
    mock_verificar.return_value = (assinatura, None, None, {})

    response = self._post()

    self.assertEqual(response.status_code, 200)
    body = json.loads(response.content)
    self.assertTrue(body.get('success'))
    mock_registrar.assert_called_once()

  @patch('crm_vendas.assinatura_publica_helpers.cache')
  @patch('crm_vendas.views_assinatura_publica.configurar_tenant_para_assinatura_publica', return_value=None)
  @patch('crm_vendas.assinatura_digital_service.enviar_pdf_final', return_value=(True, None))
  @patch('crm_vendas.assinatura_digital_service.registrar_assinatura', return_value='concluido')
  @patch('crm_vendas.assinatura_digital_service.verificar_token_assinatura')
  @patch('crm_vendas.assinatura_digital_service.normalizar_token_assinatura_url', side_effect=lambda t: t)
  @patch('crm_vendas.assinatura_publica_helpers.loads')
  def test_post_vendedor_assina_chama_enviar_pdf_final(
    self,
    mock_loads,
    _norm,
    mock_verificar,
    mock_registrar,
    mock_pdf,
    _cfg,
    mock_cache,
  ):
    mock_cache.get.return_value = 0
    mock_loads.return_value = {'loja_id': self.loja_id}
    assinatura = MagicMock()
    documento = MagicMock(__class__=type('Proposta', (), {}))
    documento.get_status_assinatura_display.return_value = 'Aguardando vendedor'
    assinatura.documento = documento
    mock_verificar.return_value = (assinatura, None, None, {})

    response = self._post()

    self.assertEqual(response.status_code, 200)
    mock_pdf.assert_called_once()
