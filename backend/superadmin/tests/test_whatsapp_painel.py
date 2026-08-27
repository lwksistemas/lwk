"""Painel WhatsApp: agrupa lojas LWK e parceiros; chave só para parceiro."""
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from superadmin.models import Loja, PlanoAssinatura, TipoLoja, WhatsappApiKey, WhatsappCustomer
from superadmin.services.whatsapp_painel_service import (
    criar_parceiro,
    documento_parceiro_valido,
    emitir_chave,
    hash_api_key,
    montar_painel,
    snapshot_evolution_item,
)

CPF_OK = "52998224725"
CNPJ_OK = "04252011000110"


def _loja(nome="Harmonis", slug="clinicaharmonis"):
    tipo = TipoLoja.objects.create(nome="Clínica", slug=f"tipo-{slug}", codigo=slug[:4].upper())
    plano = PlanoAssinatura.objects.create(nome="Full", slug=f"plano-{slug}", preco_mensal=99)
    owner = User.objects.create_user(username=f"owner-{slug}@t.com", password="senha12345")
    return Loja.objects.create(
        nome=nome, slug=slug, cpf_cnpj="37302743000126", tipo_loja=tipo, plano=plano, owner=owner, is_active=True,
    )


class SnapshotEvolutionTests(TestCase):
    def test_normaliza_status_open(self):
        snap = snapshot_evolution_item({
            "instance": {"instanceName": "lwk_loja_6", "status": "open", "ownerJid": "5516999999999@s.whatsapp.net"},
        })
        self.assertEqual(snap["instance_name"], "lwk_loja_6")
        self.assertEqual(snap["status"], "connected")
        self.assertEqual(snap["telefone"], "5516999999999")


class PainelWhatsappServiceTests(TestCase):
    def test_agrupa_instancia_lwk_na_loja(self):
        loja = _loja()
        with (
            patch("superadmin.services.whatsapp_painel_service.evolution_configured", return_value=True),
            patch(
                "superadmin.services.whatsapp_painel_service.fetch_instances",
                return_value=[{"instance": {"instanceName": f"lwk_loja_{loja.id}", "status": "open"}}],
            ),
        ):
            painel = montar_painel()
        self.assertTrue(painel["evolution"]["ok"])
        self.assertEqual(painel["resumo"]["conectados"], 1)
        cliente = next(c for c in painel["clientes"] if c["loja_id"] == loja.id)
        self.assertEqual(cliente["tipo"], "lwk_loja")
        self.assertEqual(cliente["numeros"][0]["status"], "connected")

    def test_parceiro_recebe_chave_hash(self):
        p = criar_parceiro(nome="Sistema PHP", documento=CPF_OK)
        key, raw = emitir_chave(p, nome="teste")
        self.assertTrue(raw.startswith(f"lwk_wh_{CPF_OK}_"))
        self.assertEqual(key.prefixo, f"lwk_wh_{CPF_OK}")
        self.assertEqual(key.key_hash, hash_api_key(raw))
        self.assertNotEqual(key.key_hash, raw)

    def test_exige_cpf_ou_cnpj_valido(self):
        with self.assertRaises(ValueError):
            criar_parceiro(nome="Sem doc", documento="")
        with self.assertRaises(ValueError):
            criar_parceiro(nome="CPF ruim", documento="11111111111")
        self.assertEqual(documento_parceiro_valido("529.982.247-25"), CPF_OK)
        self.assertEqual(documento_parceiro_valido("04.252.011/0001-10"), CNPJ_OK)

    def test_cpf_cnpj_unico_por_parceiro(self):
        criar_parceiro(nome="Primeiro", documento=CNPJ_OK)
        with self.assertRaises(ValueError):
            criar_parceiro(nome="Duplicado", documento="04.252.011/0001-10")

    def test_loja_lwk_nao_emite_chave(self):
        loja = _loja(slug="loja-sem-chave")
        c = WhatsappCustomer.objects.create(tipo=WhatsappCustomer.TIPO_LWK, loja=loja, nome=loja.nome)
        with self.assertRaises(ValueError):
            emitir_chave(c)


class PainelWhatsappApiTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("sa-wa@t.com", "sa-wa@t.com", "senha12345")
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    @patch("superadmin.services.whatsapp_painel_service.evolution_configured", return_value=False)
    def test_get_painel_superadmin(self, _cfg):
        res = self.client.get("/api/superadmin/whatsapp/painel/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("resumo", res.data)
        self.assertIn("clientes", res.data)

    def test_cria_parceiro_e_emite_chave(self):
        res = self.client.post(
            "/api/superadmin/whatsapp/parceiros/",
            {"nome": "Clínica XP", "documento": CPF_OK, "quota_numeros": 80},
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["documento"], CPF_OK)
        self.assertEqual(res.data["quota_numeros"], 80)
        raw = res.data["chave"]
        self.assertTrue(raw.startswith(f"lwk_wh_{CPF_OK}_"))
        me = APIClient().get("/api/whatsapp/v1/me/", HTTP_AUTHORIZATION=f"Bearer {raw}")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.data["nome"], "Clínica XP")
        self.assertEqual(me.data["documento"], CPF_OK)
        self.assertEqual(me.data["quota_numeros"], 80)

    def test_cria_parceiro_sem_documento_falha(self):
        res = self.client.post("/api/superadmin/whatsapp/parceiros/", {"nome": "Sem CNPJ"}, format="json")
        self.assertEqual(res.status_code, 400)

    def test_me_rejeita_chave_revogada(self):
        p = criar_parceiro(nome="Revogar", documento=CNPJ_OK)
        key, raw = emitir_chave(p)
        self.client.post(f"/api/superadmin/whatsapp/parceiros/{p.id}/chaves/{key.id}/revogar/")
        me = APIClient().get("/api/whatsapp/v1/me/", HTTP_AUTHORIZATION=f"Bearer {raw}")
        self.assertEqual(me.status_code, 401)
        self.assertTrue(WhatsappApiKey.objects.get(id=key.id).revoked_at)
