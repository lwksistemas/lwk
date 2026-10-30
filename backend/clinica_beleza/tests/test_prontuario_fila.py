"""O PDF do prontuário não fica gravado na tabela da fila."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, TestCase
from django_q.models import Task

from clinica_beleza.views_prontuario import _arquivar_prontuario_em_segundo_plano

PDF = b"%PDF-1.4 prontuario de teste"


class ArquivarProntuarioFilaTest(TestCase):
    @patch("clinica_beleza.media_docs_service.arquivar_pdf_gerado")
    @patch("clinica_beleza.models.Patient")
    @patch("tenants.middleware.set_current_loja_id")
    @patch("tenants.middleware._configure_tenant_db_for_loja")
    @patch("superadmin.models.Loja")
    @patch("core.task_queue.task_queue_enabled", return_value=True)
    def test_pdf_vai_para_a_midia_e_nao_fica_em_task(
        self, _enabled, loja_model, _configura, _loja_atual, patient_model, arquivar,
    ):
        from django_q import tasks as qtasks

        loja = MagicMock(id=1)
        paciente = MagicMock()
        loja_model.objects.using.return_value.filter.return_value.first.return_value = loja
        patient_model.objects.filter.return_value.first.return_value = paciente
        real_async = qtasks.async_task
        capturado = []

        def roda_na_hora(*args, **kwargs):
            capturado.append(args)
            kwargs["sync"] = True
            return real_async(*args, **kwargs)

        with patch("django_q.tasks.async_task", side_effect=roda_na_hora):
            _arquivar_prontuario_em_segundo_plano(1, 9, PDF, "prontuario.pdf")

        arquivar.assert_called_once_with(1, paciente, PDF, "prontuario.pdf")
        self.assertEqual(Task.objects.count(), 0)
        self.assertEqual(len(capturado), 1)
        self.assertNotIn(PDF, capturado[0])
        self.assertTrue(str(capturado[0][3]).startswith("prontuario-pdf:"))


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
