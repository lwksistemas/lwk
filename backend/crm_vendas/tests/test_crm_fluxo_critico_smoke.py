"""Smoke dos fluxos críticos CRM: assinatura pendente, reenvio e exports da API."""
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, SimpleTestCase

from crm_vendas.assinatura_digital_service import reenviar_link_assinatura_pendente


class CrmFluxoCriticoSmokeTest(SimpleTestCase):
    """Cadeia pipeline → proposta → assinatura (helpers sem banco)."""

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.post("/crm-vendas/propostas/1/reenviar_para_assinatura/")

    def test_reenvio_rejeita_status_nao_pendente(self):
        doc = MagicMock()
        doc.status_assinatura = "concluido"
        ok, msg, err = reenviar_link_assinatura_pendente(doc, loja_id=1, request=self.request)
        self.assertFalse(ok)
        self.assertIsNone(msg)
        self.assertIn("aguardando cliente ou vendedor", (err or "").lower())

    def test_status_pendentes_alinhados_com_frontend(self):
        pendentes = ("aguardando_cliente", "aguardando_vendedor")
        for status_assinatura in pendentes:
            with self.subTest(status=status_assinatura):
                doc = MagicMock()
                doc.status_assinatura = status_assinatura
                doc.__class__.__name__ = "Proposta"
                doc.oportunidade = None
                if status_assinatura == "aguardando_cliente":
                    ok, _msg, err = reenviar_link_assinatura_pendente(
                        doc, loja_id=1, request=self.request,
                    )
                    self.assertFalse(ok)
                    self.assertIn("oportunidade", (err or "").lower())
                else:
                    doc.canal_assinatura_vendedor = "email"
                    with patch(
                        "crm_vendas.assinatura_digital_service._email_vendedor_documento",
                        return_value="",
                    ):
                        ok, _msg, err = reenviar_link_assinatura_pendente(
                            doc, loja_id=1, request=self.request,
                        )
                        self.assertFalse(ok)
                        self.assertIn("e-mail", (err or "").lower())

    def test_exports_fluxo_assinatura_disponiveis(self):
        from crm_vendas import assinatura_digital_service as svc

        for name in (
            "criar_token_assinatura",
            "reenviar_link_assinatura_pendente",
            "verificar_token_assinatura",
            "registrar_assinatura",
        ):
            with self.subTest(symbol=name):
                self.assertTrue(hasattr(svc, name))

    def test_crm_me_campos_permissoes_documentados(self):
        """Garante que crm_me continua expondo acesso_total e permissoes (Fase 29)."""
        from pathlib import Path

        path = Path(__file__).resolve().parents[1] / "views_crm_me_dashboard.py"
        content = path.read_text(encoding="utf-8")
        self.assertIn("'acesso_total'", content)
        self.assertIn("'permissoes'", content)
