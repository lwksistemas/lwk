"""Testes das exclusões recursivas de mídia (pasta do paciente e loja inteira)."""
from unittest import TestCase
from unittest.mock import MagicMock, patch


class MediaDeleteDirTest(TestCase):
    @patch("core.media_storage.requests.delete")
    def test_delete_dir_by_url_usa_recursive(self, mock_del):
        from core.media_storage import media_delete_dir_by_url

        resp = MagicMock(status_code=200)
        mock_del.return_value = resp
        url = "https://media.lwksistemas.com.br/files/37302743000126/luiz_22239255889/pdf/a.pdf"
        self.assertTrue(media_delete_dir_by_url(url))
        called = mock_del.call_args[0][0] if mock_del.call_args[0] else mock_del.call_args.kwargs.get("url", "")
        # Remove a PASTA {paciente}/pdf, com recursive=true — nao o arquivo isolado
        self.assertIn("/upload/37302743000126/luiz_22239255889/pdf", called)
        self.assertIn("recursive=true", called)

    @patch("core.media_storage.requests.delete")
    def test_delete_dir_by_url_ignora_url_invalida(self, mock_del):
        from core.media_storage import media_delete_dir_by_url

        self.assertFalse(media_delete_dir_by_url("https://evil.com/files/x/pdf/a.pdf"))
        mock_del.assert_not_called()


class MediaDeleteTenantRootTest(TestCase):
    @patch("core.media_storage.requests.delete")
    def test_apaga_raiz_do_tenant_por_cnpj(self, mock_del):
        from core.media_storage import media_delete_tenant_root

        mock_del.return_value = MagicMock(status_code=200)
        self.assertTrue(media_delete_tenant_root("37.302.743/0001-26"))
        called = mock_del.call_args[0][0] if mock_del.call_args[0] else mock_del.call_args.kwargs.get("url", "")
        self.assertIn("/upload/37302743000126/?recursive=true", called)

    @patch("core.media_storage.requests.delete")
    def test_recusa_tenant_de_sistema(self, mock_del):
        from core.media_storage import media_delete_tenant_root

        # Nunca apagar /storage/superadmin ou /storage/suporte por engano
        self.assertFalse(media_delete_tenant_root("superadmin"))
        self.assertFalse(media_delete_tenant_root("suporte"))
        mock_del.assert_not_called()

    @patch("core.media_storage.requests.delete")
    def test_recusa_cnpj_invalido(self, mock_del):
        from core.media_storage import media_delete_tenant_root

        self.assertFalse(media_delete_tenant_root("123"))
        mock_del.assert_not_called()


class RemoverPdfMediaPrescricaoTest(TestCase):
    @patch("core.media_storage.media_delete_by_url")
    def test_apaga_pdf_url_da_prescricao(self, mock_del):
        from types import SimpleNamespace
        from clinica_beleza.views_consultas.prescricoes import remover_pdf_media_prescricao

        presc = SimpleNamespace(
            id=9,
            pdf_url="https://media.lwksistemas.com.br/files/37302743000126/luiz_222/pdf/a.pdf",
        )
        remover_pdf_media_prescricao(presc)
        mock_del.assert_called_once_with(presc.pdf_url)

    @patch("core.media_storage.media_delete_by_url")
    def test_sem_pdf_url_nao_chama(self, mock_del):
        from types import SimpleNamespace
        from clinica_beleza.views_consultas.prescricoes import remover_pdf_media_prescricao

        remover_pdf_media_prescricao(SimpleNamespace(id=1, pdf_url=""))
        mock_del.assert_not_called()
