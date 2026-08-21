"""Mensagem de orçamento no WhatsApp: resumo profissional, sem dump de cadastro."""
from decimal import Decimal
from types import SimpleNamespace
from django.test import SimpleTestCase

from clinica_beleza.orcamento_service import (
    _format_brl,
    montar_mensagem_whatsapp_orcamento,
    observacoes_para_exibicao,
)
from whatsapp.message_templates import msg_orcamento


class FormatBrlOrcamentoTest(SimpleTestCase):
    def test_milhar_e_centavos(self):
        self.assertEqual(_format_brl(Decimal("3580")), "R$ 3.580,00")
        self.assertEqual(_format_brl(Decimal("800.50")), "R$ 800,50")


class ObservacoesExibicaoTest(SimpleTestCase):
    def test_quebra_bloco_colado(self):
        bruto = (
            "Dados do Cliente: SECRETARIA MUNICIPAL Empresa: MUNICIPIO "
            "CPF/CNPJ: 24212862000146 E-mail: foo@bar.com Telefone: (38) 99999-0000 Endereço: Rua A"
        )
        out = observacoes_para_exibicao(bruto)
        self.assertIn("\nEmpresa:", out)
        self.assertIn("\nCPF/CNPJ:", out)
        self.assertIn("\nE-mail:", out)
        self.assertIn("\nTelefone:", out)
        self.assertIn("\nEndereço:", out)

    def test_preserva_quebras_existentes(self):
        t = "Linha 1\nLinha 2"
        self.assertEqual(observacoes_para_exibicao(t), t)


class MsgOrcamentoWhatsappTest(SimpleTestCase):
    def test_nao_inclui_observacoes_nem_cadastro(self):
        item = SimpleNamespace(
            nome_procedimento="BOTOX - TESTA E GLABELA",
            quantidade=1,
            subtotal=Decimal("800.00"),
        )
        orc = SimpleNamespace(
            patient=SimpleNamespace(nome="Luiz Henrique Felix"),
            professional=SimpleNamespace(nome="Dra. Ana"),
            itens=SimpleNamespace(all=lambda: [item]),
            valor_total=Decimal("3580.00"),
            validade_dias=30,
            observacoes="Dados do Cliente: SECRETARIA CNPJ 123 LGPD texto",
        )
        msg = montar_mensagem_whatsapp_orcamento(orc, "Clínica Harmonis")
        self.assertNotIn("SECRETARIA", msg)
        self.assertNotIn("CNPJ", msg)
        self.assertNotIn("LGPD", msg)
        self.assertNotIn("Obs:", msg)
        self.assertIn("Luiz Henrique Felix", msg)
        self.assertIn("Clínica Harmonis", msg)
        self.assertIn("BOTOX", msg)
        self.assertIn("3.580,00", msg)
        self.assertIn("anexo", msg.lower())

    def test_template_curto(self):
        msg = msg_orcamento(
            nome="Maria",
            loja_nome="Harmonis",
            linhas_itens=["• Botox (1x) — R$ 800,00"],
            total="R$ 800,00",
            validade_dias=30,
        )
        self.assertIn("Olá *Maria*", msg)
        self.assertIn("Harmonis", msg)
        self.assertNotIn("Dados do Cliente", msg)
