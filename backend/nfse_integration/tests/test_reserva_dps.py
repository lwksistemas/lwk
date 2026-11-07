"""Reserva do número da DPS e recusa do segundo clique igual."""
from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase, TransactionTestCase
from django.utils import timezone

from nfse_integration.persistencia_nfse_loja import (
    EmissaoJaEmAndamento,
    gerar_proximo_numero_rps,
    reservar_emissao_loja,
)
from tenants.middleware import set_current_tenant_db
from nfse_integration.queue_dispatch import enqueue_emissao_nfse_loja


class ReservaDpsTests(SimpleTestCase):
    databases = {"default"}
    @patch("nfse_integration.models.NFSe")
    def test_pendente_recente_nao_reserva_outro_numero(self, nfse):
        nota = SimpleNamespace(numero_rps=8, data_emissao=timezone.now())
        nfse.objects.select_for_update.return_value.filter.return_value = [nota]
        with self.assertRaises(EmissaoJaEmAndamento) as ctx:
            reservar_emissao_loja(
                4,
                SimpleNamespace(),
                tomador_cpf_cnpj="123",
                tomador_nome="Ana",
                tomador_email="",
                servico_descricao="Consulta",
                valor_servicos=Decimal("10.00"),
            )
        self.assertEqual(ctx.exception.numero_rps, 8)
        nfse.objects.create.assert_not_called()

    @patch("nfse_integration.models.NFSe")
    def test_reserva_o_proximo_numero_na_linha_pendente(self, nfse):
        nfse.objects.select_for_update.return_value.filter.return_value = []
        nfse.objects.filter.return_value.aggregate.return_value = {"m": 4}
        nfse.objects.create.return_value = SimpleNamespace(numero_rps=5)
        reserva = reservar_emissao_loja(
            4,
            SimpleNamespace(nacional_ultimo_dps=0, issnet_ultimo_rps_conhecido=0, provedor_nf="nacional"),
            tomador_cpf_cnpj="123",
            tomador_nome="Ana",
            tomador_email="a@b.c",
            servico_descricao="Consulta",
            valor_servicos=Decimal("10.00"),
        )
        self.assertEqual(reserva.numero_rps, 5)
        criado = nfse.objects.create.call_args.kwargs
        self.assertEqual(criado["numero_rps"], 5)
        self.assertEqual(criado["status"], "pendente")

    @patch("nfse_integration.models.NFSe")
    def test_pendente_velha_nao_emite_outra_no_mesmo_clique(self, nfse):
        antiga = MagicMock(numero_rps=3, data_emissao=timezone.now() - timedelta(minutes=20))
        nfse.objects.select_for_update.return_value.filter.return_value = [antiga]
        with self.assertRaises(EmissaoJaEmAndamento) as ctx:
            reservar_emissao_loja(
                4,
                SimpleNamespace(nacional_ultimo_dps=3, issnet_ultimo_rps_conhecido=0, provedor_nf="nacional"),
                tomador_cpf_cnpj="123",
                tomador_nome="Ana",
                tomador_email="",
                servico_descricao="Consulta",
                valor_servicos=Decimal("10.00"),
            )
        self.assertEqual(ctx.exception.numero_rps, 3)
        self.assertIn("prefeitura", str(ctx.exception))
        self.assertEqual(antiga.status, "erro")
        nfse.objects.create.assert_not_called()

    @patch("django.db.transaction.atomic")
    @patch("nfse_integration.models.NFSe")
    def test_a_trava_abre_no_banco_da_loja(self, nfse, atomic):
        nfse.objects.select_for_update.return_value.filter.return_value = []
        nfse.objects.filter.return_value.aggregate.return_value = {"m": 1}
        nfse.objects.create.return_value = SimpleNamespace(numero_rps=2)
        set_current_tenant_db("loja_teste")
        try:
            reservar_emissao_loja(
                4,
                SimpleNamespace(provedor_nf="nacional", nacional_ultimo_dps=1, issnet_ultimo_rps_conhecido=0),
                tomador_cpf_cnpj="123",
                tomador_nome="Ana",
                tomador_email="",
                servico_descricao="Consulta",
                valor_servicos=Decimal("10.00"),
            )
            gerar_proximo_numero_rps(
                4,
                SimpleNamespace(pk=1, nacional_ultimo_dps=1, issnet_ultimo_rps_conhecido=0),
            )
        finally:
            set_current_tenant_db("default")
        atomic.assert_any_call(using="loja_teste")
        for chamada in atomic.call_args_list:
            self.assertEqual(chamada.kwargs.get("using"), "loja_teste")

    def test_o_link_publico_tem_limite_por_hora(self):
        from nfse_integration.views_pdf_public import LIMITE_CONSULTA_PDF, _consulta_pdf_permitida

        memoria: dict[str, int] = {}

        class _Cache:
            def get(self, chave, default=0):
                return memoria.get(chave, default)

            def set(self, chave, valor, timeout=None):
                memoria[chave] = valor

        with patch("django.core.cache.cache", _Cache()):
            for _ in range(LIMITE_CONSULTA_PDF):
                self.assertTrue(_consulta_pdf_permitida("token-da-nota"))
            self.assertFalse(_consulta_pdf_permitida("token-da-nota"))

    def test_o_nome_da_tarefa_nao_muda_entre_processos(self):
        nomes = []

        def guarda(nome, *_args, **_kwargs):
            nomes.append(nome)

        dados = {
            "numero_rps_reservado": 9,
            "tomador_cpf_cnpj": "123",
            "valor_servicos": "10.00",
            "servico_descricao": "Consulta",
        }
        with patch("core.task_queue.enqueue_task", side_effect=guarda):
            enqueue_emissao_nfse_loja(4, dados)
            enqueue_emissao_nfse_loja(4, dados)
        self.assertEqual(nomes[0], nomes[1])
        self.assertNotIn("hash", nomes[0])


class ReservaLojaGravaErroNoBancoTests(TransactionTestCase):
    """A nota da loja mora no schema do tenant. O teste cria a tabela e usa a transação de verdade."""

    def tearDown(self):
        from tenants.middleware import set_current_loja_id, set_current_tenant_db

        set_current_loja_id(None)
        set_current_tenant_db("default")

    def test_loja_nota_velha_fica_erro_e_o_clique_seguinte_reserva(self):
        from django.db import connection

        from superadmin.models import Loja, PlanoAssinatura, TipoLoja

        from nfse_integration.models import NFSe
        from tenants.middleware import set_current_loja_id, set_current_tenant_db

        if NFSe._meta.db_table not in connection.introspection.table_names():
            with connection.schema_editor() as editor:
                editor.create_model(NFSe)

        tipo = TipoLoja.objects.create(nome="CRM Reserva", slug="tipo-reserva-nfse", codigo="RSVNF")
        plano = PlanoAssinatura.objects.create(
            nome="Plano Reserva", slug="plano-reserva-nfse", descricao="teste", preco_mensal=Decimal("10.00"),
        )
        owner = User.objects.create_user(username="dono-reserva-nfse", password="senha12345")
        loja = Loja.objects.create(
            nome="Loja Reserva", slug="loja-reserva-nfse", tipo_loja=tipo, plano=plano, owner=owner,
        )
        set_current_loja_id(loja.id)
        set_current_tenant_db("default")
        antiga = NFSe.objects.create(
            loja_id=loja.id,
            numero_nf="PENDENTE-3",
            numero_rps=3,
            data_emissao=timezone.now() - timedelta(minutes=20),
            valor=Decimal("10.00"),
            tomador_cpf_cnpj="123",
            tomador_nome="Ana",
            servico_descricao="Consulta",
            status="pendente",
            provedor="nacional",
        )
        config = SimpleNamespace(provedor_nf="nacional", nacional_ultimo_dps=3, issnet_ultimo_rps_conhecido=0)
        dados = dict(
            tomador_cpf_cnpj="123",
            tomador_nome="Ana",
            tomador_email="",
            servico_descricao="Consulta",
            valor_servicos=Decimal("10.00"),
        )
        with self.assertRaises(EmissaoJaEmAndamento):
            reservar_emissao_loja(loja.id, config, **dados)
        antiga.refresh_from_db()
        self.assertEqual(antiga.status, "erro")
        nova = reservar_emissao_loja(loja.id, config, **dados)
        self.assertEqual(nova.status, "pendente")
        self.assertNotEqual(nova.pk, antiga.pk)
        antiga.refresh_from_db()
        self.assertEqual(antiga.status, "erro")


class ReservaGravaErroNoBancoTests(TestCase):
    """A recusa da nota velha tem que ficar gravada. O raise depois do commit é o que permite emitir de novo."""

    def test_lwk_nota_velha_fica_erro_e_o_clique_seguinte_reserva(self):
        from asaas_integration.models_nfse_config import SuperadminNFSeConfig
        from superadmin.models import NFSeEmitida

        from nfse_integration.persistencia_nfse_superadmin import (
            EmissaoJaEmAndamento as RecusaLwk,
            reservar_emissao_superadmin,
        )

        config = SuperadminNFSeConfig.get_config()
        config.nacional_ultimo_dps = 364
        config.ultimo_rps = 364
        config.save(update_fields=["nacional_ultimo_dps", "ultimo_rps", "updated_at"])
        antiga = NFSeEmitida.objects.create(
            numero_nf="PENDENTE-364",
            numero_rps=364,
            valor=Decimal("12.00"),
            tomador_cpf_cnpj="123",
            tomador_nome="Ana",
            descricao_servico="Consulta",
            status="pendente",
            provedor="nacional",
        )
        NFSeEmitida.objects.filter(pk=antiga.pk).update(created_at=timezone.now() - timedelta(minutes=20))
        payload = SimpleNamespace(
            loja=None,
            tomador_cpf_cnpj="123",
            tomador_nome="Ana",
            tomador_email="",
            descricao="Consulta",
            valor=Decimal("12.00"),
        )
        with self.assertRaises(RecusaLwk):
            reservar_emissao_superadmin(config, payload)
        antiga.refresh_from_db()
        self.assertEqual(antiga.status, "erro")
        config.refresh_from_db()
        self.assertEqual(config.nacional_ultimo_dps, 364)
        nova = reservar_emissao_superadmin(config, payload)
        self.assertEqual(nova.status, "pendente")
        self.assertEqual(nova.numero_rps, 365)
        antiga.refresh_from_db()
        self.assertEqual(antiga.status, "erro")
