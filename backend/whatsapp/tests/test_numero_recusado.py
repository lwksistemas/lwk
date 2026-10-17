from datetime import datetime, timedelta, timezone as dt_timezone
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from whatsapp.numero_recusado import (
    ids_de_recusa_a_preservar,
    pular_numero_recusado,
    texto_diz_sem_whatsapp,
)


class TextoSemWhatsappTest(SimpleTestCase):
    def test_reconhece_a_mensagem_da_evolution(self):
        self.assertTrue(texto_diz_sem_whatsapp(
            {"error": "Número não encontrado no WhatsApp (5516999999999)."},
        ))

    def test_outro_erro_nao_bloqueia(self):
        self.assertFalse(texto_diz_sem_whatsapp({"error": "evolution_not_connected"}))


class PreservarRecusaTest(SimpleTestCase):
    def test_guarda_so_a_ultima_recusa_de_cada_telefone(self):
        recusa = {"error": "Número não encontrado no WhatsApp (5516999999999)."}
        linhas = [
            (3, "16999999999", "falhou", recusa),
            (2, "(16) 99999-9999", "enviado", {}),
            (1, "16988887777", "enviado", {}),
            (4, "16988887777", "falhou", recusa),
        ]
        self.assertEqual(ids_de_recusa_a_preservar(linhas), {3})


class PularNumeroRecusadoTest(SimpleTestCase):
    def test_pula_se_o_cadastro_nao_mudou_depois_da_recusa(self):
        recusa = datetime(2026, 10, 16, 18, 0, tzinfo=dt_timezone.utc)
        patient = MagicMock()
        patient.phone = "16999999999"
        patient.telefone = ""
        patient.updated_at = recusa - timedelta(days=1)
        with patch("whatsapp.numero_recusado.recusa_sem_whatsapp", return_value=recusa):
            self.assertTrue(pular_numero_recusado(patient, 6, db="loja_x"))

    def test_tenta_de_novo_se_o_cadastro_foi_alterado(self):
        recusa = datetime(2026, 10, 16, 18, 0, tzinfo=dt_timezone.utc)
        patient = MagicMock()
        patient.phone = "16988887777"
        patient.telefone = ""
        patient.updated_at = recusa + timedelta(hours=1)
        with patch("whatsapp.numero_recusado.recusa_sem_whatsapp", return_value=recusa):
            self.assertFalse(pular_numero_recusado(patient, 6, db="loja_x"))
