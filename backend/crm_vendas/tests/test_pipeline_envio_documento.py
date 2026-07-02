"""Smoke: decisão de enfileirar envio de documento (pipeline → proposta/contrato)."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from crm_vendas.models import Proposta
from crm_vendas.views_enviar_cliente import dispatch_enviar_proposta_contrato_cliente


def _instance_proposta():
    lead = MagicMock()
    lead.email = 'cliente@example.com'
    lead.telefone = '11999999999'
    opp = MagicMock()
    opp.lead_id = 1
    opp.lead = lead
    doc = MagicMock(spec=Proposta)
    doc.id = 11
    doc.loja_id = 4
    doc.oportunidade = opp
    return doc


class DispatchEnvioDocumentoTest(SimpleTestCase):
    @patch('crm_vendas.documento_envio_queue.enqueue_enviar_proposta_contrato_cliente')
    @patch('crm_vendas.documento_envio_queue._should_enqueue_documento_envio', return_value=True)
    @patch('crm_vendas.views_enviar_cliente.get_current_loja_id', return_value=4)
    @patch('crm_vendas.views_enviar_cliente.get_public_api_base_url', return_value='https://api.example.com')
    def test_enfileira_quando_fila_ativa(self, _base, _loja, _should, mock_enqueue):
        request = MagicMock()
        request.user.pk = 3
        instance = _instance_proposta()

        ok, err, queued = dispatch_enviar_proposta_contrato_cliente(instance, 'email', request)

        self.assertTrue(ok)
        self.assertIsNone(err)
        self.assertTrue(queued)
        mock_enqueue.assert_called_once()

    @patch('crm_vendas.views_enviar_cliente._enviar_proposta_contrato_cliente_sync', return_value=(True, None))
    @patch('crm_vendas.documento_envio_queue._should_enqueue_documento_envio', return_value=False)
    @patch('crm_vendas.views_enviar_cliente.get_current_loja_id', return_value=4)
    def test_envio_sync_quando_fila_desligada(self, _loja, _should, mock_sync):
        request = MagicMock()
        instance = _instance_proposta()

        ok, err, queued = dispatch_enviar_proposta_contrato_cliente(instance, 'whatsapp', request)

        self.assertTrue(ok)
        self.assertFalse(queued)
        mock_sync.assert_called_once()

    @patch('crm_vendas.views_enviar_cliente.get_current_loja_id', return_value=None)
    def test_sem_contexto_loja_falha(self, _loja):
        request = MagicMock()
        instance = _instance_proposta()

        ok, err, queued = dispatch_enviar_proposta_contrato_cliente(instance, 'email', request)

        self.assertFalse(ok)
        self.assertIn('loja', (err or '').lower())
        self.assertFalse(queued)

    def test_lead_sem_email_bloqueia_canal_email(self):
        instance = _instance_proposta()
        instance.oportunidade.lead.email = '   '
        request = MagicMock()

        with patch('crm_vendas.views_enviar_cliente.get_current_loja_id', return_value=4):
            ok, err, queued = dispatch_enviar_proposta_contrato_cliente(instance, 'email', request)

        self.assertFalse(ok)
        self.assertIn('e-mail', (err or '').lower())
        self.assertFalse(queued)
