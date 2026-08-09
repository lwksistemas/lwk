"""Testes de segurança IDOR para upload público de fotos via QR."""
import json
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from django.test import RequestFactory

from clinica_beleza.views_foto_paciente import EnviarFotoPublicaView


class EnviarFotoPublicaIdorTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = EnviarFotoPublicaView.as_view()

    @patch("superadmin.models.Loja.objects")
    @patch("clinica_beleza.views_foto_paciente.decodificar_token_foto")
    @patch("clinica_beleza.views_foto_paciente.configurar_tenant_publico_clinica")
    @patch("clinica_beleza.views_foto_paciente.Consulta.objects")
    def test_get_token_valido_retorna_dados(self, mock_consulta, mock_tenant, mock_decode, mock_loja):
        mock_decode.return_value = {
            "consulta_id": 1,
            "patient_id": 2,
            "loja_id": 3,
        }
        mock_tenant.return_value = None
        mock_loja.using.return_value.filter.return_value.first.return_value = SimpleNamespace(nome="Clínica")
        consulta = SimpleNamespace(
            id=1,
            patient_id=2,
            loja_id=3,
            status="IN_PROGRESS",
            patient=SimpleNamespace(nome="Paciente"),
            professional=SimpleNamespace(nome="Dr."),
        )
        mock_consulta.select_related.return_value.get.return_value = consulta

        request = self.factory.get("/enviar-foto/tok/")
        response = self.view(request, token="tok")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["consulta_id"], 1)

    @patch("clinica_beleza.views_foto_paciente.decodificar_token_foto")
    def test_get_token_invalido_rejeita(self, mock_decode):
        mock_decode.return_value = None
        request = self.factory.get("/enviar-foto/tok/")
        response = self.view(request, token="tok")
        self.assertEqual(response.status_code, 400)

    @patch("superadmin.models.Loja.objects")
    @patch("clinica_beleza.views_foto_paciente.decodificar_token_foto")
    @patch("clinica_beleza.views_foto_paciente.configurar_tenant_publico_clinica")
    @patch("clinica_beleza.views_foto_paciente.Consulta.objects")
    def test_get_patient_id_diferente_rejeita(self, mock_consulta, mock_tenant, mock_decode, mock_loja):
        mock_decode.return_value = {
            "consulta_id": 1,
            "patient_id": 99,
            "loja_id": 3,
        }
        mock_tenant.return_value = None
        mock_loja.using.return_value.filter.return_value.first.return_value = SimpleNamespace(nome="Clínica")
        consulta = SimpleNamespace(
            id=1,
            patient_id=2,
            loja_id=3,
            status="IN_PROGRESS",
        )
        mock_consulta.select_related.return_value.get.return_value = consulta

        request = self.factory.get("/enviar-foto/tok/")
        response = self.view(request, token="tok")
        self.assertEqual(response.status_code, 400)

    @patch("superadmin.models.Loja.objects")
    @patch("clinica_beleza.views_foto_paciente.decodificar_token_foto")
    @patch("clinica_beleza.views_foto_paciente.configurar_tenant_publico_clinica")
    @patch("clinica_beleza.views_foto_paciente.Consulta.objects")
    def test_post_com_url_json_rejeita(self, mock_consulta, mock_tenant, mock_decode, mock_loja):
        mock_decode.return_value = {
            "consulta_id": 1,
            "patient_id": 2,
            "loja_id": 3,
        }
        mock_tenant.return_value = None
        mock_loja.using.return_value.filter.return_value.first.return_value = SimpleNamespace(nome="Clínica")
        consulta = SimpleNamespace(
            id=1,
            patient_id=2,
            loja_id=3,
            status="IN_PROGRESS",
        )
        mock_consulta.get.return_value = consulta

        request = self.factory.post(
            "/enviar-foto/tok/",
            data={"url": "https://example.com/foto.jpg"},
            content_type="application/json",
        )
        response = self.view(request, token="tok")
        self.assertEqual(response.status_code, 400)
        self.assertIn("multipart", json.loads(response.content).get("error", "").lower())

    @patch("superadmin.models.Loja.objects")
    @patch("clinica_beleza.views_foto_paciente.decodificar_token_foto")
    @patch("clinica_beleza.views_foto_paciente.configurar_tenant_publico_clinica")
    @patch("clinica_beleza.views_foto_paciente.Consulta.objects")
    @patch("clinica_beleza.views_foto_paciente.upload_foto_media")
    @patch("clinica_beleza.views_foto_paciente.registrar_foto")
    @patch("clinica_beleza.views_foto_paciente.extrair_bytes_upload_request")
    def test_post_multipart_sucesso(
        self,
        mock_extrair,
        mock_registrar,
        mock_upload,
        mock_consulta,
        mock_tenant,
        mock_decode,
        mock_loja,
    ):
        mock_decode.return_value = {
            "consulta_id": 1,
            "patient_id": 2,
            "loja_id": 3,
        }
        mock_tenant.return_value = None
        mock_loja.using.return_value.filter.return_value.first.return_value = SimpleNamespace(nome="Clínica")
        consulta = SimpleNamespace(
            id=1,
            patient_id=2,
            loja_id=3,
            status="IN_PROGRESS",
        )
        mock_consulta.get.return_value = consulta
        mock_extrair.return_value = b"imagem"
        mock_upload.return_value = {
            "secure_url": "https://media.lwksistemas.com.br/files/00000000000000/fotos/foto.jpg",
            "public_id": "00000000000000/fotos/foto.jpg",
        }
        mock_registrar.return_value = {"id": 1, "url": "https://media.lwksistemas.com.br/files/00000000000000/fotos/foto.jpg"}

        request = self.factory.post("/enviar-foto/tok/", data={"file": b"imagem"})
        response = self.view(request, token="tok")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.content)["success"])

    @patch("superadmin.models.Loja.objects")
    @patch("clinica_beleza.views_foto_paciente.decodificar_token_foto")
    @patch("clinica_beleza.views_foto_paciente.configurar_tenant_publico_clinica")
    @patch("clinica_beleza.views_foto_paciente.Consulta.objects")
    @patch("clinica_beleza.views_foto_paciente.extrair_bytes_upload_request")
    def test_post_foto_url_cloudinary_rejeita_validacao(
        self,
        mock_extrair,
        mock_consulta,
        mock_tenant,
        mock_decode,
        mock_loja,
    ):
        mock_decode.return_value = {
            "consulta_id": 1,
            "patient_id": 2,
            "loja_id": 3,
        }
        mock_tenant.return_value = None
        mock_loja.using.return_value.filter.return_value.first.return_value = SimpleNamespace(nome="Clínica")
        consulta = SimpleNamespace(
            id=1,
            patient_id=2,
            loja_id=3,
            status="IN_PROGRESS",
        )
        mock_consulta.get.return_value = consulta
        mock_extrair.return_value = None

        request = self.factory.post(
            "/enviar-foto/tok/",
            data={"url": "https://res.cloudinary.com/exemplo/foto.jpg"},
            content_type="application/json",
        )
        response = self.view(request, token="tok")
        self.assertEqual(response.status_code, 400)
