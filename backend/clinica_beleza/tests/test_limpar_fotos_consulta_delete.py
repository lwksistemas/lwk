"""Testes: limpeza de fotos no media ao excluir consulta."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase


class LimparFotosMediaConsultaTests(SimpleTestCase):
    @patch("clinica_beleza.foto_paciente_service.persistence.excluir_foto_media", return_value=True)
    @patch("core.media_storage.media_delete_by_url", return_value=False)
    def test_remove_via_excluir_foto_media(self, mock_by_url, mock_excluir):
        from clinica_beleza.foto_paciente_service.persistence import limpar_fotos_media_da_consulta

        consulta = SimpleNamespace(pk=10, loja_id=7)
        foto = SimpleNamespace(
            id=1,
            url="https://media.lwksistemas.com.br/files/12345678901/fotos/a.jpg",
            public_id="",
            loja_id=7,
        )
        loja = SimpleNamespace(id=7)
        qs = MagicMock()
        qs.only.return_value = [foto]

        with patch(
            "clinica_beleza.models.PacienteFotoAcompanhamento.objects"
        ) as foto_objects, patch("superadmin.models.Loja.objects") as loja_objects:
            foto_objects.filter.return_value = qs
            loja_objects.using.return_value.filter.return_value.first.return_value = loja
            n = limpar_fotos_media_da_consulta(consulta)

        self.assertEqual(n, 1)
        mock_excluir.assert_called_once_with(loja, foto.url, "")
        mock_by_url.assert_not_called()

    @patch("clinica_beleza.foto_paciente_service.persistence.excluir_foto_media", return_value=False)
    @patch("core.media_storage.media_delete_by_url", return_value=True)
    def test_fallback_media_delete_by_url(self, mock_by_url, mock_excluir):
        from clinica_beleza.foto_paciente_service.persistence import limpar_fotos_media_da_consulta

        consulta = SimpleNamespace(pk=11, loja_id=7)
        foto = SimpleNamespace(
            id=2,
            url="https://media.lwksistemas.com.br/files/12345678901/fotos/b.jpg",
            public_id="",
            loja_id=7,
        )
        qs = MagicMock()
        qs.only.return_value = [foto]

        with patch(
            "clinica_beleza.models.PacienteFotoAcompanhamento.objects"
        ) as foto_objects, patch("superadmin.models.Loja.objects") as loja_objects:
            foto_objects.filter.return_value = qs
            loja_objects.using.return_value.filter.return_value.first.return_value = None
            n = limpar_fotos_media_da_consulta(consulta)

        self.assertEqual(n, 1)
        mock_excluir.assert_not_called()
        mock_by_url.assert_called_once_with(foto.url)
