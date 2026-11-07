"""Reserva do número da DPS e recusa do segundo clique igual."""
from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
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
    def test_pendente_velha_libera_um_numero_novo(self, nfse):
        antiga = MagicMock(numero_rps=3, data_emissao=timezone.now() - timedelta(minutes=10))
        nfse.objects.select_for_update.return_value.filter.return_value = [antiga]
        nfse.objects.filter.return_value.aggregate.return_value = {"m": 3}
        nfse.objects.create.return_value = SimpleNamespace(numero_rps=4)
        reservar_emissao_loja(
            4,
            SimpleNamespace(nacional_ultimo_dps=3, issnet_ultimo_rps_conhecido=0, provedor_nf="nacional"),
            tomador_cpf_cnpj="123",
            tomador_nome="Ana",
            tomador_email="",
            servico_descricao="Consulta",
            valor_servicos=Decimal("10.00"),
        )
        self.assertEqual(antiga.status, "erro")
        self.assertEqual(nfse.objects.create.call_args.kwargs["numero_rps"], 4)

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
