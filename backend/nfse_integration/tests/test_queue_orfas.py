"""Worker marca 'Emitindo' como erro se a emissão estoura."""
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from nfse_integration.queue_tasks import _marcar_pendente_como_erro, run_emissao_nfse_loja


class QueueOrfasTest(SimpleTestCase):
    @patch("nfse_integration.persistencia_nfse_loja.registrar_falha_emissao_loja")
    def test_marcar_pendente_usa_numero_reservado(self, registrar):
        _marcar_pendente_como_erro(
            7,
            {
                "numero_rps_reservado": 42,
                "tomador_cpf_cnpj": "123",
                "tomador_nome": "A",
                "tomador_email": "a@b.com",
                "servico_descricao": "X",
                "valor_servicos": "10.00",
            },
            "boom",
        )
        registrar.assert_called_once()
        kwargs = registrar.call_args.kwargs
        self.assertEqual(kwargs["loja_id"], 7)
        self.assertEqual(kwargs["numero_rps"], 42)
        self.assertEqual(kwargs["valor_servicos"], Decimal("10.00"))
        self.assertEqual(kwargs["erro_msg"], "boom")

    @patch("nfse_integration.persistencia_nfse_loja.registrar_falha_emissao_loja")
    def test_sem_reserva_nao_grava(self, registrar):
        _marcar_pendente_como_erro(7, {}, "boom")
        registrar.assert_not_called()

    @patch("nfse_integration.queue_tasks._marcar_pendente_como_erro")
    @patch("nfse_integration.loja_nfse_api.processar_emissao_nfse_loja_sync", side_effect=RuntimeError("x"))
    @patch("tenants.middleware.get_current_tenant_db", return_value="loja_x")
    @patch("tenants.middleware._configure_tenant_db_for_loja", return_value=True)
    @patch("superadmin.models.Loja")
    def test_excecao_apos_tenant_marca_erro(
        self, loja_model, _cfg, _db, _proc, marcar,
    ):
        loja_model.objects.using.return_value.filter.return_value.first.return_value = MagicMock(id=9)
        with self.assertRaises(RuntimeError):
            run_emissao_nfse_loja(9, {"numero_rps_reservado": 3, "valor_servicos": "1"})
        marcar.assert_called_once()
        self.assertEqual(marcar.call_args.args[0], 9)
