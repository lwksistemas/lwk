"""Testes da fila de sync Google Calendar para atividades CRM."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase


class ActivitiesGoogleSyncQueueTest(SimpleTestCase):
    @patch("core.task_queue.enqueue_task")
    def test_enqueue_create(self, mock_enqueue):
        from crm_vendas.activities_google_sync_queue import enqueue_sync_atividade_create

        enqueue_sync_atividade_create(2, 99, 7)
        mock_enqueue.assert_called_once()
        self.assertIn("crm-gcal-create-99", mock_enqueue.call_args.args[0])

    @patch("core.task_queue.enqueue_task")
    def test_enqueue_update(self, mock_enqueue):
        from crm_vendas.activities_google_sync_queue import enqueue_sync_atividade_update

        enqueue_sync_atividade_update(2, 10, None)
        mock_enqueue.assert_called_once()
        self.assertIn("crm-gcal-update-10", mock_enqueue.call_args.args[0])

    @patch("core.task_queue.enqueue_task")
    def test_enqueue_delete(self, mock_enqueue):
        from crm_vendas.activities_google_sync_queue import enqueue_sync_atividade_delete

        enqueue_sync_atividade_delete(2, "evt-abc", 5)
        mock_enqueue.assert_called_once()
        self.assertIn("crm-gcal-delete", mock_enqueue.call_args.args[0])

    @patch("crm_vendas.activities_google_sync_queue.enqueue_sync_atividade_create")
    def test_dispatch_create_sem_atividade(self, mock_enqueue):
        from crm_vendas.activities_google_sync_queue import dispatch_sync_atividade_create

        dispatch_sync_atividade_create(MagicMock(), None)
        mock_enqueue.assert_not_called()

    @patch("crm_vendas.activities_google_sync_queue.enqueue_sync_atividade_create")
    @patch("crm_vendas.utils.get_current_vendedor_id", return_value=3)
    def test_dispatch_create_com_atividade(self, _mock_vid, mock_enqueue):
        from crm_vendas.activities_google_sync_queue import dispatch_sync_atividade_create

        atividade = MagicMock(loja_id=4, id=11)
        dispatch_sync_atividade_create(MagicMock(), atividade)
        mock_enqueue.assert_called_once_with(4, 11, 3)

    @patch("crm_vendas.activities_google_sync.sync_atividade_create_for_context")
    @patch("crm_vendas.models.Atividade")
    @patch("crm_vendas.activities_google_sync_queue._setup_tenant", return_value=True)
    def test_run_create_worker(self, _tenant, mock_model, mock_sync):
        from crm_vendas.activities_google_sync_queue import run_sync_atividade_create

        atividade = MagicMock()
        mock_model.objects.filter.return_value.first.return_value = atividade

        run_sync_atividade_create(2, 99, 7)

        mock_sync.assert_called_once_with(atividade, vendedor_id=7)

    @patch("crm_vendas.activities_google_sync.sync_atividade_create_for_context")
    @patch("crm_vendas.activities_google_sync_queue._setup_tenant", return_value=False)
    def test_run_create_sem_tenant(self, _tenant, mock_sync):
        from crm_vendas.activities_google_sync_queue import run_sync_atividade_create

        run_sync_atividade_create(2, 99, None)
        mock_sync.assert_not_called()


class ActivitiesGoogleSyncContextTest(SimpleTestCase):
    @patch("crm_vendas.activities_google_sync.push_atividade_to_google", return_value="evt-1")
    @patch("crm_vendas.activities_google_sync._get_connection")
    def test_create_for_context_salva_event_id(self, mock_conn, mock_push):
        from crm_vendas.activities_google_sync import sync_atividade_create_for_context

        mock_conn.return_value = MagicMock()
        atividade = MagicMock(loja_id=2, id=5, google_event_id="")
        sync_atividade_create_for_context(atividade, vendedor_id=3)
        self.assertEqual(atividade.google_event_id, "evt-1")
        atividade.save.assert_called_once_with(update_fields=["google_event_id"])

    @patch("crm_vendas.activities_google_sync._get_connection", return_value=None)
    @patch("crm_vendas.activities_google_sync.push_atividade_to_google")
    def test_create_sem_conexao_nao_falha(self, mock_push, _conn):
        from crm_vendas.activities_google_sync import sync_atividade_create_for_context

        atividade = MagicMock(loja_id=2)
        sync_atividade_create_for_context(atividade, vendedor_id=None)
        mock_push.assert_not_called()
