"""Testa excluir_prescritor (DELETE) e recadastrar_prescritor da integração Memed.

Garante: o DELETE usa o external_id que a Memed reporta para o CPF (que pode
divergir do gerado pelo sistema), o tratamento de 404 como sucesso idempotente,
e que recadastrar chama delete + create.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings


def _prof():
    return SimpleNamespace(
        id=2,
        loja_id=9,
        nome="FERNANDO MARUM MAUAD",
        cpf="268.107.068-60",
        email="f@example.com",
        telefone="16999999999",
        data_nascimento=None,
        sexo="M",
        conselho="CRM",
        registro_profissional="113233",
        conselho_uf="SP",
    )


@override_settings(MEMED_API_KEY="k", MEMED_SECRET_KEY="s")
class ExcluirPrescritorTest(SimpleTestCase):
    @patch("clinica_beleza.memed_service.requests.delete")
    @patch("clinica_beleza.memed_service._external_id_memed_por_cpf", return_value="lwk-loja16-prof1")
    def test_delete_usa_external_id_reportado_pela_memed(self, _mock_lookup, mock_delete):
        from clinica_beleza.memed_service import excluir_prescritor

        resp = MagicMock()
        resp.status_code = 204
        resp.text = ""
        mock_delete.return_value = resp

        out = excluir_prescritor(_prof())
        self.assertTrue(out["ok"])
        # Excluiu o external_id que a Memed tinha (loja16), NÃO o do sistema (loja9)
        self.assertEqual(out["external_id"], "lwk-loja16-prof1")
        args, kwargs = mock_delete.call_args
        url = args[0] if args else kwargs.get("url", "")
        self.assertIn("/sinapse-prescricao/usuarios/lwk-loja16-prof1", url)

    @patch("clinica_beleza.memed_service.requests.delete")
    @patch("clinica_beleza.memed_service._external_id_memed_por_cpf", return_value=None)
    def test_delete_404_e_idempotente(self, _mock_lookup, mock_delete):
        from clinica_beleza.memed_service import excluir_prescritor

        resp = MagicMock()
        resp.status_code = 404
        resp.text = "not found"
        mock_delete.return_value = resp

        out = excluir_prescritor(_prof())
        self.assertTrue(out["ok"])
        self.assertTrue(out["not_found"])
        # Sem lookup, cai no external_id do sistema (loja9)
        self.assertEqual(out["external_id"], "lwk-loja9-prof2")

    def test_delete_sem_cpf_valido_skip(self):
        from clinica_beleza.memed_service import excluir_prescritor

        prof = _prof()
        prof.cpf = "123"
        out = excluir_prescritor(prof)
        self.assertFalse(out["ok"])
        self.assertEqual(out.get("skipped"), "sem_cpf_valido")


@override_settings(MEMED_API_KEY="k", MEMED_SECRET_KEY="s")
class CpfEhPrescritorNaMemedTest(SimpleTestCase):
    @patch("clinica_beleza.memed_service.requests.get")
    def test_cpf_de_prescritor_retorna_true(self, mock_get):
        from clinica_beleza.memed_service import cpf_e_prescritor_na_memed

        resp = MagicMock()
        resp.status_code = 200  # existe prescritor com esse CPF
        mock_get.return_value = resp
        self.assertTrue(cpf_e_prescritor_na_memed("22239255889"))

    @patch("clinica_beleza.memed_service.requests.get")
    def test_cpf_sem_prescritor_retorna_false(self, mock_get):
        from clinica_beleza.memed_service import cpf_e_prescritor_na_memed

        resp = MagicMock()
        resp.status_code = 404  # ninguém cadastrado com esse CPF (caso normal)
        mock_get.return_value = resp
        self.assertFalse(cpf_e_prescritor_na_memed("36971645898"))

    def test_cpf_invalido_retorna_false_sem_chamar_api(self):
        from clinica_beleza.memed_service import cpf_e_prescritor_na_memed

        self.assertFalse(cpf_e_prescritor_na_memed("123"))

    @patch("clinica_beleza.memed_service.requests.get", side_effect=Exception("rede"))
    def test_falha_de_rede_retorna_false(self, _mock_get):
        from clinica_beleza.memed_service import cpf_e_prescritor_na_memed
        import requests as _rq

        # A funcao captura requests.RequestException; simular esse tipo.
        with patch("clinica_beleza.memed_service.requests.get",
                   side_effect=_rq.RequestException("timeout")):
            self.assertFalse(cpf_e_prescritor_na_memed("22239255889"))


@override_settings(MEMED_API_KEY="k", MEMED_SECRET_KEY="s")
class RecadastrarPrescritorTest(SimpleTestCase):
    @patch("clinica_beleza.memed_service.sincronizar_prescritor")
    @patch("clinica_beleza.memed_service.excluir_prescritor")
    def test_recadastrar_chama_delete_e_create(self, mock_excluir, mock_sinc):
        from clinica_beleza.memed_service import recadastrar_prescritor

        mock_excluir.return_value = {"ok": True, "status": 204}
        mock_sinc.return_value = {"ok": True, "status": 201, "external_id": "lwk-loja9-prof2"}

        out = recadastrar_prescritor(_prof())
        self.assertTrue(out["delete"]["ok"])
        self.assertTrue(out["create"]["ok"])
        mock_excluir.assert_called_once()
        # Recadastro sempre força o envio (ignora MEMED_AUTO_CADASTRO)
        _, kwargs = mock_sinc.call_args
        self.assertTrue(kwargs.get("force"))
