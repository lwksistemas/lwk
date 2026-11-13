"""Número e validade comercial da proposta, sem outra sequência."""
from datetime import date, datetime
from types import SimpleNamespace
from unittest import TestCase

from crm_vendas.proposta_identificacao import (
    comercialmente_vencida,
    fim_validade_comercial,
    frase_contratacao,
    numero_proposta_exibicao,
    texto_prazo_link,
    texto_validade_comercial,
)


class NumeroPropostaTest(TestCase):
    def test_usa_o_numero_gravado_e_o_ano_de_criacao(self):
        proposta = SimpleNamespace(numero="335", id=9, created_at=datetime(2026, 11, 12))
        self.assertEqual(numero_proposta_exibicao(proposta), "335/2026")

    def test_tira_o_zero_a_esquerda_sem_criar_outro_numero(self):
        proposta = SimpleNamespace(numero="007", id=7, created_at=date(2026, 1, 2))
        self.assertEqual(numero_proposta_exibicao(proposta), "7/2026")

    def test_proposta_assinada_nao_vence_e_mantem_o_numero(self):
        proposta = SimpleNamespace(
            numero="217",
            id=4,
            created_at=date(2026, 1, 1),
            data_envio=None,
            validade_inicio=date(2026, 1, 1),
            validade_dias=7,
            status_assinatura="concluido",
        )
        self.assertEqual(numero_proposta_exibicao(proposta), "217/2026")
        self.assertFalse(comercialmente_vencida(proposta, date(2026, 11, 13)))
        self.assertIn("registrada", texto_validade_comercial(proposta))

    def test_sem_assinatura_o_prazo_encerra_e_nao_muda_o_numero(self):
        proposta = SimpleNamespace(
            numero="216",
            id=5,
            created_at=date(2026, 10, 1),
            data_envio=None,
            validade_inicio=None,
            validade_dias=15,
            status_assinatura="aguardando_cliente",
            valor_total="1000",
        )
        self.assertEqual(fim_validade_comercial(proposta), date(2026, 10, 16))
        self.assertTrue(comercialmente_vencida(proposta, date(2026, 11, 13)))
        self.assertEqual(numero_proposta_exibicao(proposta), "216/2026")
        self.assertEqual(proposta.valor_total, "1000")

    def test_sem_validade_o_link_continua_de_sete_dias(self):
        proposta = SimpleNamespace(validade_dias=None, validade_inicio=None, data_envio=None, created_at=None)
        self.assertEqual(texto_prazo_link(proposta), "por 7 dias")

    def test_o_link_vai_ate_o_fim_da_validade_comercial(self):
        from datetime import timedelta as delta

        from crm_vendas.proposta_identificacao import LinkComercialEncerrado, delta_token_assinatura

        proposta = SimpleNamespace(
            numero="218",
            validade_dias=7,
            validade_inicio=date(2026, 11, 13),
            data_envio=None,
            created_at=date(2026, 11, 13),
            status_assinatura="rascunho",
        )
        self.assertEqual(texto_prazo_link(proposta), "até 20/11/2026")
        self.assertEqual(texto_validade_comercial(proposta, date(2026, 11, 13)), "Validade comercial: 7 dias, até 20/11/2026.")
        prazo = delta_token_assinatura(proposta, "cliente", datetime(2026, 11, 13, 12, 0))
        self.assertGreater(prazo, delta(days=6))
        self.assertLess(prazo, delta(days=8))
        with self.assertRaises(LinkComercialEncerrado):
            delta_token_assinatura(proposta, "cliente", datetime(2026, 11, 21, 8, 0))

    def test_frase_dos_servicos_cita_a_prestadora(self):
        texto = frase_contratacao(
            "Sistema de Laudos • Captura DICOM • Worklist",
            "Ultrasis Sistemas Médicos",
        )
        self.assertEqual(
            texto,
            "Preparamos sua proposta comercial para contratação do Sistema de Laudos, "
            "com Captura DICOM e Worklist, da Ultrasis Sistemas Médicos.",
        )
