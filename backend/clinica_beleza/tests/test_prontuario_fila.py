"""O PDF do prontuário não fica gravado na tabela da fila."""
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase
from django_q.models import Task

from clinica_beleza.views_prontuario import _arquivar_prontuario_em_segundo_plano

PDF = b"%PDF-1.4 prontuario de teste"


class ArquivarProntuarioFilaTest(TestCase):
    @patch("core.task_queue.task_queue_enabled", return_value=True)
    def test_pdf_nao_aparece_em_task(self, _enabled):
        from django_q import tasks as qtasks

        real_async = qtasks.async_task

        def roda_na_hora(*args, **kwargs):
            kwargs["sync"] = True
            return real_async(*args, **kwargs)

        with patch("django_q.tasks.async_task", side_effect=roda_na_hora):
            _arquivar_prontuario_em_segundo_plano(1, 9, PDF, "prontuario.pdf")

        self.assertEqual(Task.objects.count(), 0)
        for tarefa in Task.objects.all():
            self.assertNotIn(PDF, tarefa.args or ())


class ArquivarProntuarioSemFilaTest(SimpleTestCase):
    @patch("threading.Thread")
    @patch("core.task_queue.task_queue_enabled", return_value=False)
    def test_usa_thread_quando_a_fila_esta_desligada(self, _enabled, mock_thread):
        _arquivar_prontuario_em_segundo_plano(1, 9, PDF, "prontuario.pdf")
        mock_thread.assert_called_once()
        kwargs = mock_thread.call_args.kwargs
        self.assertEqual(kwargs["args"][2], PDF)
        self.assertTrue(kwargs["daemon"])
        mock_thread.return_value.start.assert_called_once()
