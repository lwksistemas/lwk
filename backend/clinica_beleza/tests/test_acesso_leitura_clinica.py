"""Quem abre prontuário, prescrição ou foto deixa usuário, paciente e hora."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from clinica_beleza.acesso_leitura import registrar_leitura_clinica
from clinica_beleza.views_foto_paciente import ConsultaFotosPacienteView
from clinica_beleza.views_prontuario import ProntuarioView


class RegistroLeituraTest(SimpleTestCase):
    @patch("superadmin.models.HistoricoAcessoGlobal")
    @patch("superadmin.models.Loja")
    @patch("tenants.middleware.get_current_loja_id", return_value=6)
    @patch("superadmin.historico_usuario.resolver_identidade_historico")
    def test_grava_usuario_paciente_e_recurso(self, identidade, _loja_id, loja_model, historico):
        user = SimpleNamespace(pk=4, email="ana@clinica.test")
        identidade.return_value = (user, "ana@clinica.test", "Ana", 6)
        loja_model.objects.using.return_value.filter.return_value.first.return_value = SimpleNamespace(
            nome="Harmonis", slug="harmonis",
        )
        request = APIRequestFactory().get(
            "/api/clinica-beleza/patients/9/prontuario/",
            HTTP_X_FORWARDED_FOR="203.0.113.9, 198.51.100.20",
        )
        registrar_leitura_clinica(request, 9, "Prontuário")
        gravado = historico.objects.using.return_value.create.call_args.kwargs
        self.assertEqual(gravado["user"], user)
        self.assertEqual(gravado["recurso_id"], 9)
        self.assertEqual(gravado["recurso"], "Prontuário")
        self.assertEqual(gravado["acao"], "visualizar")
        self.assertEqual(gravado["ip_address"], "198.51.100.20")

    def test_falha_do_historico_nao_quebra_a_leitura(self):
        request = APIRequestFactory().get("/api/clinica-beleza/patients/9/prontuario/")
        with patch(
            "superadmin.historico_usuario.resolver_identidade_historico",
            side_effect=RuntimeError("banco"),
        ):
            registrar_leitura_clinica(request, 9, "Prontuário")


class ProntuarioRegistraLeituraTest(SimpleTestCase):
    @patch("clinica_beleza.views_prontuario.registrar_leitura_clinica")
    @patch("clinica_beleza.views_prontuario.ProntuarioSectionSerializer")
    @patch("clinica_beleza.views_prontuario.listar_prontuario_paciente", return_value={})
    @patch("clinica_beleza.views_prontuario.Patient.objects")
    def test_abertura_chama_o_registro(self, patients, _lista, serializer, registrar):
        patients.filter.return_value.exists.return_value = True
        serializer.return_value.data = {"secoes": []}
        request = Request(APIRequestFactory().get("/api/clinica-beleza/patients/9/prontuario/"))
        response = ProntuarioView().get(request, 9)
        self.assertEqual(response.status_code, 200)
        registrar.assert_called_once_with(request, 9, "Prontuário")

    @patch("clinica_beleza.views_prontuario.registrar_leitura_clinica")
    @patch("clinica_beleza.views_prontuario.Patient.objects")
    def test_paciente_ausente_nao_registra(self, patients, registrar):
        patients.filter.return_value.exists.return_value = False
        request = Request(APIRequestFactory().get("/api/clinica-beleza/patients/9/prontuario/"))
        response = ProntuarioView().get(request, 9)
        self.assertEqual(response.status_code, 404)
        registrar.assert_not_called()


class FotosRegistramLeituraTest(SimpleTestCase):
    @patch("clinica_beleza.views_foto_paciente.limites_fotos_consulta", return_value={})
    @patch("clinica_beleza.views_foto_paciente.listar_fotos_paciente", return_value=[])
    @patch("clinica_beleza.views_foto_paciente.registrar_leitura_clinica")
    def test_lista_de_fotos_registra_o_paciente(self, registrar, _fotos, _limites):
        view = ConsultaFotosPacienteView()
        view.get_object = MagicMock(return_value=SimpleNamespace(
            patient_id=9, patient=SimpleNamespace(nome="Paciente"), id=3, loja_id=6,
        ))
        request = APIRequestFactory().get("/api/clinica-beleza/consultas/3/fotos/")
        response = view.get(request, 3)
        self.assertEqual(response.status_code, 200)
        registrar.assert_called_once_with(request, 9, "Fotos do paciente")
