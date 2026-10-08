"""Link de assinatura por WhatsApp quando o cliente não tem e-mail."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from crm_vendas.assinatura_digital_token import criar_token_assinatura


class TokenSemEmailTest(SimpleTestCase):
    @patch("crm_vendas.models.AssinaturaDigital.objects")
    def test_cliente_sem_email_grava_texto_vazio(self, objects):
        objects.create.return_value = MagicMock(id=1)

        class Proposta:
            id = 303
            oportunidade = SimpleNamespace(
                lead=SimpleNamespace(nome="BRENDA BARBOSA DA SILVA", email=None),
            )

        criar_token_assinatura(Proposta(), "cliente", 4)

        self.assertEqual(objects.create.call_args.kwargs["email_assinante"], "")
        self.assertEqual(objects.create.call_args.kwargs["nome_assinante"], "BRENDA BARBOSA DA SILVA")
        self.assertEqual(objects.create.call_args.kwargs["proposta"].id, 303)
