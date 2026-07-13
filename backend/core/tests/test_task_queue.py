"""Testes da fila django-q (enqueue + fallback)."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from core.q_cluster_settings import parse_redis_url
from core.task_queue import enqueue_task


class ParseRedisUrlTest(SimpleTestCase):
    def test_url_com_usuario_e_senha(self):
        cfg = parse_redis_url("redis://default:secret@redis.internal:6379/0")
        self.assertEqual(cfg["host"], "redis.internal")
        self.assertEqual(cfg["port"], 6379)
        self.assertEqual(cfg["password"], "secret")
        self.assertEqual(cfg["username"], "default")

    def test_url_sem_credenciais(self):
        cfg = parse_redis_url("redis://redis.internal:6379/1")
        self.assertEqual(cfg["host"], "redis.internal")
        self.assertEqual(cfg["db"], 1)
        self.assertNotIn("password", cfg)


@override_settings(USE_TASK_QUEUE=True)
class EnqueueTaskFallbackTest(SimpleTestCase):
    @patch("core.task_queue._resolve_callable")
    @patch("django_q.tasks.async_task", side_effect=Exception("redis down"))
    def test_fallback_sync_quando_fila_falha(self, _async, mock_resolve):
        mock_func = MagicMock(return_value="ok")
        mock_resolve.return_value = mock_func

        result = enqueue_task("test-task", "some.module.run", 1, loja_id=4)

        self.assertEqual(result, "ok")
        mock_func.assert_called_once_with(1, loja_id=4)
