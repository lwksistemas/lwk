"""Testes unitários para prontuario_pdf.py — função _resolver_cabecalho.
"""
from unittest.mock import MagicMock, patch

from django.test import TestCase

from clinica_beleza.prontuario_pdf import _resolver_cabecalho


class ResolverCabecalhoTest(TestCase):
    """Testes para a função _resolver_cabecalho (prioridade de cabeçalho)."""

    @patch("clinica_beleza.prontuario_pdf.header.MemedTimbrado.objects")
    def test_retorna_timbrado_quando_pdf_existe(self, mock_timbrado_qs):
        """Deve retornar ('timbrado', bytes) quando MemedTimbrado tem PDF."""
        timbrado = MagicMock()
        timbrado.pdf = b"%PDF-1.4 fake content"
        mock_timbrado_qs.filter.return_value.first.return_value = timbrado

        tipo, dados = _resolver_cabecalho(loja_id=1)

        self.assertEqual(tipo, "timbrado")
        self.assertEqual(dados, b"%PDF-1.4 fake content")
        mock_timbrado_qs.filter.assert_called_once_with(loja_id=1)

    @patch("clinica_beleza.prontuario_pdf.header.MemedTimbrado.objects")
    @patch("superadmin.models.Loja.objects")
    def test_retorna_logo_quando_sem_timbrado_mas_tem_logo(self, mock_loja_qs, mock_timbrado_qs):
        """Deve retornar ('logo', url) quando não há timbrado mas Loja tem logo."""
        mock_timbrado_qs.filter.return_value.first.return_value = None

        loja = MagicMock()
        loja.logo = "https://cdn.example.com/logo.png"
        mock_loja_qs.filter.return_value.first.return_value = loja

        tipo, dados = _resolver_cabecalho(loja_id=2)

        self.assertEqual(tipo, "logo")
        self.assertEqual(dados, "https://cdn.example.com/logo.png")

    @patch("clinica_beleza.prontuario_pdf.header.MemedTimbrado.objects")
    @patch("superadmin.models.Loja.objects")
    def test_retorna_texto_quando_sem_timbrado_e_sem_logo(self, mock_loja_qs, mock_timbrado_qs):
        """Deve retornar ('texto', loja) quando não há timbrado nem logo."""
        mock_timbrado_qs.filter.return_value.first.return_value = None

        loja = MagicMock()
        loja.logo = ""
        mock_loja_qs.filter.return_value.first.return_value = loja

        tipo, dados = _resolver_cabecalho(loja_id=3)

        self.assertEqual(tipo, "texto")
        self.assertEqual(dados, loja)

    @patch("clinica_beleza.prontuario_pdf.header.MemedTimbrado.objects")
    @patch("superadmin.models.Loja.objects")
    def test_retorna_texto_quando_loja_nao_existe(self, mock_loja_qs, mock_timbrado_qs):
        """Deve retornar ('texto', None) quando a loja não existe no banco."""
        mock_timbrado_qs.filter.return_value.first.return_value = None
        mock_loja_qs.filter.return_value.first.return_value = None

        tipo, dados = _resolver_cabecalho(loja_id=999)

        self.assertEqual(tipo, "texto")
        self.assertIsNone(dados)

    @patch("clinica_beleza.prontuario_pdf.header.MemedTimbrado.objects")
    def test_timbrado_com_pdf_vazio_nao_usa_timbrado(self, mock_timbrado_qs):
        """Se MemedTimbrado existe mas pdf é vazio/None, deve fallback para logo/texto."""
        timbrado = MagicMock()
        timbrado.pdf = None
        mock_timbrado_qs.filter.return_value.first.return_value = timbrado

        with patch("superadmin.models.Loja.objects") as mock_loja_qs:
            loja = MagicMock()
            loja.logo = "https://cdn.example.com/logo.png"
            mock_loja_qs.filter.return_value.first.return_value = loja

            tipo, dados = _resolver_cabecalho(loja_id=4)

        self.assertEqual(tipo, "logo")
        self.assertEqual(dados, "https://cdn.example.com/logo.png")

    @patch("clinica_beleza.prontuario_pdf.header.MemedTimbrado.objects")
    def test_timbrado_com_pdf_bytes_vazios_nao_usa_timbrado(self, mock_timbrado_qs):
        """Se MemedTimbrado existe mas pdf é b'', deve fallback para logo/texto."""
        timbrado = MagicMock()
        timbrado.pdf = b""
        mock_timbrado_qs.filter.return_value.first.return_value = timbrado

        with patch("superadmin.models.Loja.objects") as mock_loja_qs:
            loja = MagicMock()
            loja.logo = ""
            loja.nome = "Clínica Teste"
            mock_loja_qs.filter.return_value.first.return_value = loja

            tipo, dados = _resolver_cabecalho(loja_id=5)

        self.assertEqual(tipo, "texto")
        self.assertEqual(dados, loja)

    @patch("clinica_beleza.prontuario_pdf.header.MemedTimbrado.objects")
    def test_prioridade_timbrado_sobre_logo(self, mock_timbrado_qs):
        """Mesmo que Loja tenha logo, se MemedTimbrado tem PDF, usa timbrado."""
        timbrado = MagicMock()
        timbrado.pdf = b"%PDF content"
        mock_timbrado_qs.filter.return_value.first.return_value = timbrado

        # Nem deve chegar a consultar Loja
        tipo, dados = _resolver_cabecalho(loja_id=6)

        self.assertEqual(tipo, "timbrado")
        self.assertEqual(dados, b"%PDF content")
