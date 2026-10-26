"""Número do WhatsApp e leitura da resposta de confirmação. Sem chamar a Evolution."""
from django.test import SimpleTestCase

from whatsapp.evolution_client import (
    _candidate_whatsapp_numbers,
    _prefer_br_mobile_digits,
    evolution_instance_name,
    loja_id_from_evolution_instance,
)
from whatsapp.message_templates import msg_assinatura_cliente, msg_lembrete_agendamento
from whatsapp.views_evolution_webhook import (
    _extract_button_id,
    _extract_message_text,
    _extract_phone_from_jid,
    _normalize_reply_text,
)


class NumeroEvolutionTests(SimpleTestCase):
    def test_celular_ganha_55_e_o_nono_digito(self):
        candidatos = _candidate_whatsapp_numbers("(16) 3333-4444")
        self.assertIn("1633334444", candidatos)
        self.assertIn("551633334444", candidatos)
        self.assertIn("5516933334444", candidatos)

    def test_devolve_o_nove_quando_a_evolution_corta(self):
        self.assertEqual(_prefer_br_mobile_digits("5562999792267", "556299792267"), "5562999792267")
        self.assertEqual(_prefer_br_mobile_digits("5516981402966", "5516981402966"), "5516981402966")

    def test_nome_da_instancia_volta_para_o_id_da_loja(self):
        self.assertEqual(loja_id_from_evolution_instance(evolution_instance_name(4)), 4)
        self.assertIsNone(loja_id_from_evolution_instance("outra"))


class RespostaConfirmacaoTests(SimpleTestCase):
    def test_le_telefone_e_texto_do_botao(self):
        self.assertEqual(_extract_phone_from_jid("5516981402966@s.whatsapp.net"), "5516981402966")
        self.assertEqual(_normalize_reply_text("  Sim, confirmo!  "), "sim confirmo")
        texto = _extract_message_text(
            {"buttonsResponseMessage": {"selectedDisplayText": "Confirmar"}},
        )
        self.assertEqual(texto, "Confirmar")
        botao = _extract_button_id(
            {"templateButtonReplyMessage": {"selectedButtonId": "confirmar"}},
        )
        self.assertEqual(botao, "confirmar")
        self.assertEqual(_extract_message_text("nao-e-dict"), "")

    def test_texto_de_assinatura_e_lembrete_citam_o_nome(self):
        assinatura = msg_assinatura_cliente(
            nome="Ana",
            tipo_doc="Proposta",
            titulo="Plano mensal",
            loja_nome="Felix",
            link="https://exemplo/assinar",
        )
        self.assertIn("Ana", assinatura)
        self.assertIn("Felix", assinatura)
        self.assertIn("https://exemplo/assinar", assinatura)
        self.assertNotIn("R$", assinatura)
        lembrete = msg_lembrete_agendamento(nome="Ana", hora="10:00", procedimento="Consulta")
        self.assertIn("10:00", lembrete)
        self.assertIn("Consulta", lembrete)

    def test_mensagem_de_proposta_sai_sem_valor_e_sem_caixa_alta(self):
        texto = msg_assinatura_cliente(
            nome="RENATA SILVEIRA OLIMPIO DE PAULA FURTADO",
            tipo_doc="Proposta",
            titulo="RENATA SILVEIRA OLIMPIO DE PAULA FURTADO",
            loja_nome="FELIX REPRESENTACOES E COMERCIO LTDA",
            link="https://api.lwksistemas.com.br/r/rUjhnFZn",
            vendedor_nome="LUIZ HENRIQUE FELIX",
        )
        self.assertIn("*Felix Representacoes e Comercio Ltda*", texto)
        self.assertIn("Proposta comercial", texto)
        self.assertIn("Olá, Renata.", texto)
        self.assertIn("Renata Silveira Olimpio de Paula Furtado", texto)
        self.assertIn("*Vendedor*\nLuiz Henrique Felix", texto)
        self.assertNotIn("R$", texto)
        self.assertNotIn("🔐", texto)
        self.assertNotIn("RENATA", texto)
