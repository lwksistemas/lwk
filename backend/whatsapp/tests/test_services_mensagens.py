"""Telefone, texto de confirmação e envio simulado. Não chama a Evolution nem a Meta."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from whatsapp.models import WhatsAppConfig
from whatsapp.services import (
    _evolution_ready,
    _normalize_phone,
    _render_mensagem_template,
    _resolve_whatsapp_credentials,
    _send_whatsapp_meta,
    msg_cobranca,
    msg_confirmacao,
    msg_lembrete,
)


def _agendamento(*, modulo="clinica_beleza", nome="Ana"):
    ag = MagicMock()
    ag.patient.name = nome
    ag.patient.nome = nome
    ag.professional.nome = "Dra. Lia"
    ag.procedures.exists.return_value = False
    ag.procedure = None
    ag.whatsapp_modulo = modulo
    return ag


class TelefoneWhatsappTests(SimpleTestCase):
    def test_celular_brasileiro_ganha_codigo_do_pais(self):
        self.assertEqual(_normalize_phone("(16) 98140-2966"), "5516981402966")
        self.assertEqual(_normalize_phone("1633334444"), "551633334444")

    def test_numero_curto_e_zero_a_esquerda_depois_do_55(self):
        self.assertIsNone(_normalize_phone("123"))
        self.assertIsNone(_normalize_phone(""))
        self.assertEqual(_normalize_phone("55016981402966"), "5516981402966")


class MensagensAgendaTests(SimpleTestCase):
    def test_template_substitui_o_nome(self):
        self.assertEqual(_render_mensagem_template("Oi {nome}", {"nome": "Ana"}), "Oi Ana")
        self.assertEqual(_render_mensagem_template("Oi {nome}", {"nome": ""}), "Oi ")

    def test_cobranca_formata_valor_com_virgula(self):
        texto = msg_cobranca(SimpleNamespace(name="Ana"), 10.5)
        self.assertIn("Ana", texto)
        self.assertIn("R$ 10,50", texto)

    @patch("clinica_beleza.agenda_display.format_agenda_hora", return_value="10:00")
    @patch("clinica_beleza.agenda_display.format_agenda_data", return_value="12/10/2026")
    def test_confirmacao_usa_texto_da_loja(self, _data, _hora):
        config = SimpleNamespace(mensagem_confirmacao_agenda="Olá {nome}, {hora}. {link}")
        texto = msg_confirmacao(_agendamento(), config=config, link_confirmacao="https://exemplo/c")
        self.assertEqual(texto, "Olá Ana, 10:00. https://exemplo/c")

    @patch("clinica_beleza.agenda_display.format_agenda_hora", return_value="15:30")
    def test_lembrete_da_clinica_cita_o_horario(self, _hora):
        texto = msg_lembrete(_agendamento())
        self.assertIn("Ana", texto)
        self.assertIn("15:30", texto)


class EnvioSimuladoTests(SimpleTestCase):
    def test_evolution_desconectada_nao_esta_pronta(self):
        config = SimpleNamespace(
            whatsapp_ativo=True,
            whatsapp_provider=WhatsAppConfig.PROVIDER_EVOLUTION,
            whatsapp_connection_status=WhatsAppConfig.CONNECTION_DISCONNECTED,
            evolution_instance_name="lwk_loja_4",
            loja_id=4,
        )
        ok, err = _evolution_ready(config)
        self.assertFalse(ok)
        self.assertIn("QR", err)

    def test_credencial_meta_da_loja_exige_phone_e_token(self):
        config = SimpleNamespace(
            whatsapp_provider=WhatsAppConfig.PROVIDER_META,
            whatsapp_ativo=True,
            whatsapp_phone_id="",
            whatsapp_token="",
        )
        phone_id, token, _url, err = _resolve_whatsapp_credentials(config)
        self.assertIsNone(phone_id)
        self.assertIsNone(token)
        self.assertIn("Phone Number ID", err)

    @patch("whatsapp.services._write_whatsapp_log")
    @patch("whatsapp.services.requests.post")
    def test_meta_recusa_numero_fora_da_lista_de_teste(self, post, _log):
        resposta = MagicMock()
        resposta.ok = False
        resposta.headers = {"content-type": "application/json"}
        resposta.json.return_value = {
            "error": {"code": 131030, "message": "Recipient not in allowed list"},
        }
        post.return_value = resposta
        config = SimpleNamespace(
            whatsapp_provider=WhatsAppConfig.PROVIDER_META,
            whatsapp_ativo=True,
            whatsapp_phone_id="123",
            whatsapp_token="tok",
            loja_id=4,
        )
        ok, err = _send_whatsapp_meta("16981402966", "Olá", config=config)
        self.assertFalse(ok)
        self.assertIn("lista de números permitidos", err)
        post.assert_called_once()
