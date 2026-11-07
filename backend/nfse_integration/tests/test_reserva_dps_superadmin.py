"""Reserva do DPS da LWK e recusa do segundo clique na emissão manual."""
from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from django.utils import timezone

from nfse_integration.emissao_manual_types import EmissaoManualPayload
from nfse_integration.emissao_nacional_superadmin import emitir_manual_nacional_superadmin
from nfse_integration.persistencia_nfse_superadmin import EmissaoJaEmAndamento, reservar_emissao_superadmin
from nfse_integration.queue_dispatch import enqueue_emitir_nfse_manual


def _payload(**extra) -> EmissaoManualPayload:
    dados = dict(
        loja=None,
        tomador_cpf_cnpj="41449198000172",
        tomador_nome="Felix",
        tomador_email="",
        tomador_endereco={},
        valor=Decimal("12.00"),
        descricao="teste",
        codigo_cnae="",
        codigo_servico="",
    )
    dados.update(extra)
    return EmissaoManualPayload(**dados)


class ReservaDpsSuperadminTests(SimpleTestCase):
    databases = {"default"}

    def _config(self, travada):
        manager = MagicMock()
        manager.select_for_update.return_value.get.return_value = travada

        class Config:
            pk = 1
            nacional_ultimo_dps = 364
            ultimo_rps = 364

            class objects:
                @staticmethod
                def using(_nome):
                    return manager

        return Config()

    @patch("superadmin.models.NFSeEmitida")
    def test_segundo_clique_igual_nao_reserva_outro_numero(self, nfse):
        nota = SimpleNamespace(numero_rps=364, created_at=timezone.now())
        nfse.objects.select_for_update.return_value.filter.return_value = [nota]
        travada = SimpleNamespace(nacional_ultimo_dps=364, save=MagicMock())
        with self.assertRaises(EmissaoJaEmAndamento) as ctx:
            reservar_emissao_superadmin(self._config(travada), _payload())
        self.assertEqual(ctx.exception.numero_rps, 364)
        travada.save.assert_not_called()
        nfse.objects.create.assert_not_called()

    @patch("superadmin.models.NFSeEmitida")
    def test_reserva_o_numero_seguinte_sem_pular(self, nfse):
        nfse.objects.select_for_update.return_value.filter.return_value = []
        nfse.objects.create.return_value = SimpleNamespace(numero_rps=365)
        travada = SimpleNamespace(
            nacional_ultimo_dps=364,
            nacional_serie_dps="1",
            aliquota_iss=2,
            save=MagicMock(),
        )
        reserva = reservar_emissao_superadmin(self._config(travada), _payload())
        self.assertEqual(reserva.numero_rps, 365)
        self.assertEqual(travada.nacional_ultimo_dps, 365)
        self.assertEqual(nfse.objects.create.call_args.kwargs["status"], "pendente")

    @patch("superadmin.models.NFSeEmitida")
    def test_pendente_velha_libera_o_proximo(self, nfse):
        antiga = MagicMock(numero_rps=360, created_at=timezone.now() - timedelta(minutes=10))
        nfse.objects.select_for_update.return_value.filter.return_value = [antiga]
        nfse.objects.create.return_value = SimpleNamespace(numero_rps=365)
        travada = SimpleNamespace(
            nacional_ultimo_dps=364,
            nacional_serie_dps="1",
            aliquota_iss=2,
            save=MagicMock(),
        )
        reservar_emissao_superadmin(self._config(travada), _payload())
        self.assertEqual(antiga.status, "erro")
        self.assertEqual(nfse.objects.create.call_args.kwargs["numero_rps"], 365)

    @patch("nfse_integration.emissao_issnet_nacional_loja._resolver_p_tot_trib_sn", return_value=None)
    @patch("nfse_integration.emissao_issnet_nacional_loja.codigo_tributacao_nacional_sefin", return_value="140101")
    @patch("nfse_integration.emissao_nacional_superadmin.salvar_nfse_erro_nacional_superadmin")
    @patch("nfse_integration.nacional.NacionalClient")
    @patch("core.encryption.decrypt_value", return_value="senha")
    def test_emissao_usa_o_numero_reservado(self, _decrypt, cliente, salvar_erro, _codigo, _trib):
        config = MagicMock()
        config.nacional_certificado = b"cert"
        config.nacional_senha_certificado = "enc"
        config.nacional_codigo_municipio = "3543402"
        config.nacional_ambiente = "producao"
        config.nacional_serie_dps = "1"
        cliente.return_value.emitir_nfse.return_value = {"success": False, "error": "recusada"}
        salvar_erro.return_value = SimpleNamespace(id=1)
        emitir_manual_nacional_superadmin(config, _payload(numero_dps_reservado=365))
        config.proximo_dps.assert_not_called()
        self.assertEqual(cliente.return_value.emitir_nfse.call_args.kwargs["numero_dps"], 365)

    def test_o_nome_da_tarefa_nao_muda_entre_processos(self):
        nomes = []

        def guarda(nome, *_args, **_kwargs):
            nomes.append(nome)

        with patch("core.task_queue.enqueue_task", side_effect=guarda):
            enqueue_emitir_nfse_manual(_payload(numero_dps_reservado=365))
            enqueue_emitir_nfse_manual(_payload(numero_dps_reservado=365))
        self.assertEqual(nomes[0], nomes[1])
        self.assertTrue(nomes[0].startswith("nfse-manual-"))
