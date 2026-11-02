from django.core.cache import cache
from django.test import SimpleTestCase, TestCase

from homepage.models import SolicitacaoContato
from homepage.serializers import HeroSerializer


class ContatoSiteTests(TestCase):
    def setUp(self):
        cache.clear()

    def _post(self, ip=None, **extra):
        dados = {
            "nome": "Ana",
            "whatsapp": "16999998888",
            "produto": "crm-vendas",
            "mensagem": "Oi",
            "aceite_lgpd": True,
        }
        cabecalhos = {"HTTP_X_FORWARDED_FOR": ip} if ip else {}
        return self.client.post("/api/site/contato/", {**dados, **extra}, content_type="application/json", **cabecalhos)

    def test_limite_e_por_ip_do_cliente_e_nao_do_proxy(self):
        """Regressão: todos chegam com o mesmo REMOTE_ADDR (gateway Docker); o limite é por IP real."""
        for _ in range(8):
            self.assertEqual(self._post(ip="203.0.113.1").status_code, 201)
        self.assertEqual(self._post(ip="203.0.113.1").status_code, 429)
        # outro visitante, mesmo REMOTE_ADDR do proxy, não é bloqueado
        self.assertEqual(self._post(ip="203.0.113.2").status_code, 201)

    def test_ip_forjado_no_inicio_do_cabecalho_nao_burla_o_limite(self):
        for i in range(8):
            self._post(ip=f"10.0.0.{i}, 203.0.113.9")
        self.assertEqual(self._post(ip="10.9.9.9, 203.0.113.9").status_code, 429)

    def test_mensagem_gigante_e_recusada(self):
        self.assertEqual(self._post(mensagem="x" * 2001).status_code, 400)

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
