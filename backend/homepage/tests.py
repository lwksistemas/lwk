from django.test import SimpleTestCase, TestCase

from homepage.models import SolicitacaoContato
from homepage.serializers import HeroSerializer


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


class AnimacoesHomeTests(SimpleTestCase):
    def test_limpa_efeito_e_limite_de_duracao(self):
        limpo = HeroSerializer().validate_animacoes({
            "igual_celular": True,
            "computador": {"titulo": {"efeito": "typing", "ativo": True, "duracao": 9000, "repetir": True}},
        })
        self.assertTrue(limpo["igual_celular"])
        self.assertEqual(limpo["computador"]["titulo"]["efeito"], "typing")
        self.assertEqual(limpo["computador"]["titulo"]["duracao"], 3000)
        self.assertEqual(limpo["computador"]["imagens"]["transicao"], "fade")
        self.assertEqual(limpo["celular"]["titulo"]["efeito"], "typing")
        self.assertTrue(limpo["computador"]["titulo"]["celular"])
