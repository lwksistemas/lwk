"""Regressão do OAuth Google Calendar: PKCE precisa ficar desativado.

'auth' e 'callback' são requisições HTTP separadas e cada uma cria um Flow novo
via get_flow(). Se o PKCE estiver ativo, o code_verifier gerado no auth se perde
no callback e o Google recusa a troca de token com
"(invalid_grant) Missing code verifier". Estes testes garantem que:
1. get_flow() retorna um Flow com autogenerate_code_verifier=False;
2. authorization_url() não inclui code_challenge (portanto o callback não
   precisará de code_verifier).
"""
from django.test import SimpleTestCase, override_settings

from crm_vendas.google_calendar_service import get_flow

REDIRECT = "https://lwksistemas.com.br/api/crm-vendas/google-calendar/callback/"


@override_settings(GOOGLE_CLIENT_ID="cid.apps.googleusercontent.com", GOOGLE_CLIENT_SECRET="secret")
class GoogleCalendarPkceTest(SimpleTestCase):
    def test_get_flow_desativa_pkce(self):
        flow = get_flow(REDIRECT)
        self.assertFalse(flow.autogenerate_code_verifier)
        self.assertIsNone(flow.code_verifier)

    def test_authorization_url_nao_envia_code_challenge(self):
        flow = get_flow(REDIRECT)
        auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")
        self.assertNotIn("code_challenge", auth_url)
        # Sem verifier gerado, o callback não precisará dele.
        self.assertIsNone(flow.code_verifier)
