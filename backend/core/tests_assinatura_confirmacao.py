"""A reabertura do link mostra quem assinou, a data e o horário."""
from datetime import datetime

from django.test import SimpleTestCase
from django.utils import timezone

from core.assinatura_confirmacao import confirmacao_assinatura


class ConfirmacaoAssinaturaTests(SimpleTestCase):
    def test_proposta_traz_nome_data_e_hora(self):
        quando = timezone.make_aware(datetime(2026, 10, 24, 9, 28))
        dados = confirmacao_assinatura(
            "Proposta",
            "LUIZ HENRIQUE FELIX",
            quando,
            tipo_documento="proposta",
        )
        self.assertTrue(dados["ja_assinado"])
        self.assertEqual(dados["nome_cliente"], "LUIZ HENRIQUE FELIX")
        self.assertEqual(dados["data"], "24/10/2026")
        self.assertEqual(dados["hora"], "09:28")
        self.assertEqual(
            dados["mensagem"],
            "Proposta assinada digitalmente por LUIZ HENRIQUE FELIX em 24/10/2026 às 09:28.",
        )

    def test_termo_usa_assinado(self):
        quando = timezone.make_aware(datetime(2026, 10, 24, 15, 4))
        dados = confirmacao_assinatura("Termo", "Ana Souza", quando, tipo_documento="termo")
        self.assertIn("Termo assinado digitalmente por Ana Souza", dados["mensagem"])
        self.assertIn("24/10/2026 às 15:04", dados["mensagem"])
