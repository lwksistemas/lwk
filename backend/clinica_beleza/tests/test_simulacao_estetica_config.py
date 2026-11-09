"""Simulação estética: chave individual e somente no plano que libera a função."""
from django.test import SimpleTestCase

from clinica_beleza.simulacao_estetica_service import chave_youcam_valida
from clinica_beleza.tests.tenant_test_case import ClinicaBelezaIntegrationTestCase
from core.encryption import is_encrypted

CHAVE = "youcam-chave-clinica-teste-001"


class ChaveYouCamTest(SimpleTestCase):
    def test_rejeita_curta_espaco_e_mascara(self):
        self.assertFalse(chave_youcam_valida("curta"))
        self.assertFalse(chave_youcam_valida("youcam chave com espaco 123456"))
        self.assertFalse(chave_youcam_valida("youcam-chave-mascarada...123456"))

    def test_aceita_chave_continua(self):
        self.assertTrue(chave_youcam_valida(CHAVE))


class SimulacaoEsteticaConfigApiTests(ClinicaBelezaIntegrationTestCase):
    url = "/api/clinica-beleza/simulacao-estetica/config/"

    def test_plano_sem_recurso_nao_grava_chave(self):
        client = self.api_client_as_owner()
        headers = self.tenant_headers()

        leitura = client.get(self.url, **headers)
        self.assertEqual(leitura.status_code, 200, leitura.content)
        self.assertFalse(leitura.json()["disponivel"])
        self.assertFalse(leitura.json()["chave_configurada"])

        gravacao = client.patch(self.url, {"api_key": CHAVE, "ativa": True}, format="json", **headers)
        self.assertEqual(gravacao.status_code, 403, gravacao.content)

    def test_plano_completo_grava_chave_cifrada_so_nesta_clinica(self):
        self.plano.tem_simulacao_estetica = True
        self.plano.save(update_fields=["tem_simulacao_estetica"])
        client = self.api_client_as_owner()
        headers = self.tenant_headers()

        sem_chave = client.patch(self.url, {"ativa": True}, format="json", **headers)
        self.assertEqual(sem_chave.status_code, 400, sem_chave.content)

        gravacao = client.patch(
            self.url,
            {"api_key": CHAVE, "ativa": True},
            format="json",
            **headers,
        )
        self.assertEqual(gravacao.status_code, 200, gravacao.content)
        corpo = gravacao.json()
        self.assertTrue(corpo["disponivel"])
        self.assertTrue(corpo["ativa"])
        self.assertTrue(corpo["chave_configurada"])
        self.assertNotIn(CHAVE, gravacao.content.decode())

        from clinica_beleza.models import SimulacaoEsteticaConfig

        salva = SimulacaoEsteticaConfig.objects.get()
        self.assertTrue(is_encrypted(salva.api_key))
        self.assertEqual(salva.loja_id, self.loja.id)

        self.activate_loja(self.loja_b)
        outra = client.get(self.url, **self.tenant_headers(self.loja_b))
        self.assertEqual(outra.status_code, 200, outra.content)
        self.assertFalse(outra.json()["chave_configurada"])
        self.assertFalse(outra.json()["ativa"])
