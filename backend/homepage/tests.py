from django.test import TestCase

from homepage.models import SolicitacaoContato


class ContatoSiteTests(TestCase):
    def test_grava_pedido_com_aceite(self):
        resposta = self.client.post(
            "/api/site/contato/",
            {
                "nome": "Ana",
                "empresa": "Clínica Exemplo",
                "whatsapp": "16999998888",
                "produto": "crm-vendas",
                "mensagem": "Quero ver o CRM.",
                "origem": "demonstracao",
                "aceite_lgpd": True,
            },
            content_type="application/json",
        )
        self.assertEqual(resposta.status_code, 201)
        pedido = SolicitacaoContato.objects.get()
        self.assertEqual(pedido.produto, "crm-vendas")
        self.assertEqual(pedido.whatsapp, "16999998888")

    def test_recusa_sem_aceite_e_produto_invalido(self):
        resposta = self.client.post(
            "/api/site/contato/",
            {
                "nome": "Ana",
                "whatsapp": "16999998888",
                "produto": "desconhecido",
                "mensagem": "Oi",
                "aceite_lgpd": False,
            },
            content_type="application/json",
        )
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(SolicitacaoContato.objects.count(), 0)
