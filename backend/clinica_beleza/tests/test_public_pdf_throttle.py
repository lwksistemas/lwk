"""PDF público com throttle; pagamento não muda status/valor pelo PUT."""
from types import SimpleNamespace

from django.test import SimpleTestCase

from clinica_beleza.serializers.financeiro import PaymentSerializer
from clinica_beleza.throttles import PublicPdfThrottle
from clinica_beleza.views_assinatura_consentimento_internas import TermoConsentimentoPdfPublicView
from clinica_beleza.views_financeiro import ReciboImagemPublicView, ReciboPdfPublicView
from clinica_beleza.views_orcamento import OrcamentoImagemPublicView, OrcamentoPDFPublicView
from clinica_beleza.views_pedido_compra import PedidoCompraImagemPublicView, PedidoCompraPdfPublicView


class TestPublicPdfThrottle(SimpleTestCase):
    def test_quatro_endpoints_publicos_usam_o_mesmo_throttle(self):
        for view in (
            OrcamentoPDFPublicView,
            OrcamentoImagemPublicView,
            ReciboPdfPublicView,
            ReciboImagemPublicView,
            PedidoCompraPdfPublicView,
            PedidoCompraImagemPublicView,
            TermoConsentimentoPdfPublicView,
        ):
            self.assertEqual(view.throttle_classes, [PublicPdfThrottle])
        self.assertEqual(PublicPdfThrottle.rate, "30/min")


class TestPaymentSerializerNaoAlteraStatus(SimpleTestCase):
    def test_status_e_comissao_sao_somente_leitura(self):
        serializer = PaymentSerializer()
        for name in ("status", "comissao_percentual", "comissao_valor", "created_at"):
            self.assertTrue(serializer.fields[name].read_only, name)

    def test_put_nao_grava_status_nem_valor(self):
        instance = SimpleNamespace(
            appointment=SimpleNamespace(id=1),
            amount="100.00",
            valor_total="100.00",
            desconto="0.00",
            status="PENDING",
            comissao_percentual=0,
            comissao_valor="0.00",
        )
        serializer = PaymentSerializer(instance=instance)
        for name in ("appointment", "amount", "valor_total", "desconto", "status"):
            self.assertTrue(serializer.fields[name].read_only, name)

    def test_status_no_payload_e_ignorado_na_validacao(self):
        instance = SimpleNamespace(
            status="PENDING",
            notes="ok",
            payment_method="PIX",
            payment_date=None,
            appointment=None,
            amount=None,
            valor_total=None,
            desconto=None,
            comissao_percentual=0,
            comissao_valor=None,
            created_at=None,
            updated_at=None,
        )
        serializer = PaymentSerializer(
            instance=instance,
            data={"status": "PAID", "notes": "ajuste"},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertNotIn("status", serializer.validated_data)
        self.assertEqual(serializer.validated_data.get("notes"), "ajuste")
