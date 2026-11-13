"""Número e validade comercial da proposta, sem outra sequência."""
from datetime import date, datetime
from types import SimpleNamespace
from unittest import TestCase

from crm_vendas.proposta_identificacao import (
    comercialmente_vencida,
    fim_validade_comercial,
    frase_contratacao,
    numero_proposta_exibicao,
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
