"""Testes da fila de envio proposta/contrato ao cliente."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from crm_vendas.documento_envio_queue import (
    _should_enqueue_documento_envio,
    enqueue_enviar_proposta_contrato_cliente,
    run_enviar_proposta_contrato_cliente,
)


class ShouldEnqueueDocumentoEnvioTest(SimpleTestCase):
    @patch('crm_vendas.documento_sync_context.documento_envio_sync_only')
    @patch('core.task_queue.task_queue_enabled', return_value=True)
    def test_enfileira_quando_fila_habilitada(self, _enabled, mock_ctx):
        mock_ctx.get.return_value = False
        self.assertTrue(_should_enqueue_documento_envio())

    @patch('crm_vendas.documento_sync_context.documento_envio_sync_only')
    @patch('core.task_queue.task_queue_enabled', return_value=False)
    def test_nao_enfileira_sem_fila(self, _enabled, mock_ctx):
        mock_ctx.get.return_value = False
        self.assertFalse(_should_enqueue_documento_envio())

    @patch('crm_vendas.documento_sync_context.documento_envio_sync_only')
    @patch('core.task_queue.task_queue_enabled', return_value=True)
    def test_nao_enfileira_em_contexto_sync(self, _enabled, mock_ctx):
        mock_ctx.get.return_value = True
        self.assertFalse(_should_enqueue_documento_envio())


class EnqueueEnviarDocumentoTest(SimpleTestCase):
    @patch('core.task_queue.enqueue_task')
    def test_enqueue_proposta(self, mock_enqueue):
        enqueue_enviar_proposta_contrato_cliente(
            tipo='proposta',
            doc_id=10,
            loja_id=4,
            canal='email',
            user_id=7,
            public_api_base_url='https://api.example.com',
        )
        mock_enqueue.assert_called_once()
        args = mock_enqueue.call_args.args
        self.assertEqual(args[0], 'crm-doc-proposta-10-email')
        self.assertIn('run_enviar_proposta_contrato_cliente', args[1])


@override_settings(DATABASES={'default': {}, 'loja_test': {}})
class RunEnviarDocumentoWorkerTest(SimpleTestCase):
    @patch('crm_vendas.documento_envio_queue.close_old_connections')
    @patch('crm_vendas.documento_envio_queue._setup_tenant', return_value=False)
    def test_loja_indisponivel(self, _setup, _close):
        ok, err = run_enviar_proposta_contrato_cliente(
            'proposta', 1, 4, 'email', None, 'https://api.example.com',
        )
        self.assertFalse(ok)
        self.assertIn('indisponível', (err or '').lower())

    @patch('crm_vendas.views_enviar_cliente._enviar_proposta_contrato_cliente_sync', return_value=(True, None))
    @patch('crm_vendas.documento_envio_queue._setup_tenant', return_value=True)
    @patch('crm_vendas.documento_envio_queue.close_old_connections')
    def test_envio_proposta_sucesso(self, _close, _setup, mock_enviar):
        proposta = MagicMock()
        with patch('crm_vendas.models.Proposta') as mock_cls:
            mock_cls.objects.filter.return_value.select_related.return_value.prefetch_related.return_value.first.return_value = proposta
            ok, err = run_enviar_proposta_contrato_cliente(
                'proposta', 5, 4, 'whatsapp', None, 'https://api.example.com',
            )
        self.assertTrue(ok)
        self.assertIsNone(err)
        mock_enviar.assert_called_once()

    @patch('crm_vendas.documento_envio_queue._setup_tenant', return_value=True)
    @patch('crm_vendas.documento_envio_queue.close_old_connections')
    def test_tipo_invalido(self, _close, _setup):
        ok, err = run_enviar_proposta_contrato_cliente(
            'orcamento', 1, 4, 'email', None, 'https://api.example.com',
        )
        self.assertFalse(ok)
        self.assertIn('inválido', (err or '').lower())

    @patch('crm_vendas.documento_envio_queue._setup_tenant', return_value=True)
    @patch('crm_vendas.documento_envio_queue.close_old_connections')
    def test_documento_nao_encontrado(self, _close, _setup):
        with patch('crm_vendas.models.Contrato') as mock_cls:
            mock_cls.objects.filter.return_value.select_related.return_value.prefetch_related.return_value.first.return_value = None
            ok, err = run_enviar_proposta_contrato_cliente(
                'contrato', 99, 4, 'email', None, 'https://api.example.com',
            )
        self.assertFalse(ok)
        self.assertIn('não encontrado', (err or '').lower())
