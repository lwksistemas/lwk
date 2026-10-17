import json
import time
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from django.http import JsonResponse
from django.test import RequestFactory, SimpleTestCase

from core.middleware.midia_assinada import MidiaAssinadaMiddleware, TTL_EXIBICAO_SEGUNDOS

URL = "https://media.lwksistemas.com.br/files/37302743000126/paciente-id9/fotos/abc.jpg"


class MidiaAssinadaMiddlewareTest(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.token = patch("core.media_storage.MEDIA_API_TOKEN", "segredo-teste")
        self.token.start()
        self.addCleanup(self.token.stop)

    def test_resposta_assina_foto_por_duas_horas(self):
        mw = MidiaAssinadaMiddleware(lambda request: JsonResponse({"foto_url": URL, "nome": "Ana"}))
        request = self.factory.get("/api/clinica-beleza/patients/9/")
        response = mw(request)
        corpo = json.loads(response.content)
        self.assertEqual(corpo["nome"], "Ana")
        assinada = corpo["foto_url"]
        self.assertTrue(assinada.startswith(URL + "?"))
        exp = int(parse_qs(urlparse(assinada).query)["e"][0])
        self.assertAlmostEqual(exp - time.time(), TTL_EXIBICAO_SEGUNDOS, delta=5)

    def test_resposta_mantem_assinatura_que_ainda_vale(self):
        from core.media_storage import assinar_url_midia

        longa = assinar_url_midia(URL, ttl_seconds=21 * 24 * 3600)
        mw = MidiaAssinadaMiddleware(lambda request: JsonResponse({"url": longa}))
        response = mw(self.factory.get("/api/superadmin/backup/"))
        corpo = json.loads(response.content)
        self.assertEqual(corpo["url"], longa)

    def test_pedido_grava_caminho_sem_assinatura(self):
        from core.media_storage import assinar_url_midia

        assinada = assinar_url_midia(URL, ttl_seconds=600)
        visto = {}

        def view(request):
            visto["corpo"] = json.loads(request.body)
            return JsonResponse({"ok": True})

        mw = MidiaAssinadaMiddleware(view)
        request = self.factory.put(
            "/api/clinica-beleza/patients/9/",
            data=json.dumps({"foto_url": assinada}),
            content_type="application/json",
        )
        mw(request)
        self.assertEqual(visto["corpo"]["foto_url"], URL)

    def test_ignora_link_que_nao_e_midia(self):
        mw = MidiaAssinadaMiddleware(
            lambda request: JsonResponse({"link": "https://lwksistemas.com.br/assinar-recibo/abc"})
        )
        response = mw(self.factory.get("/api/x/"))
        corpo = json.loads(response.content)
        self.assertEqual(corpo["link"], "https://lwksistemas.com.br/assinar-recibo/abc")
