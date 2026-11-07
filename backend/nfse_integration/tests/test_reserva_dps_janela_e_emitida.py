"""Janela de 15 minutos da emissão e repetição da fila sobre um DPS já emitido.

Os testes gravam no banco de teste e leem a linha de novo. Mock não prova que a
marcação ficou gravada nem que a prefeitura deixou de ser chamada.
"""
from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from nfse_integration.persistencia_nfse_loja import EmissaoJaEmAndamento, reservar_emissao_loja
from nfse_integration.persistencia_nfse_superadmin import (
    EmissaoJaEmAndamento as RecusaLwk,
)
from nfse_integration.persistencia_nfse_superadmin import (
    reservar_emissao_superadmin,
)


class _Chamou(Exception):
    """A prefeitura foi chamada. Num caso que não devia, o teste falha."""


def _loja_com_tabela(sufixo: str):
    from django.db import connection

    from nfse_integration.models import NFSe
    from superadmin.models import Loja, PlanoAssinatura, TipoLoja
    from tenants.middleware import set_current_loja_id, set_current_tenant_db

    if NFSe._meta.db_table not in connection.introspection.table_names():
        with connection.schema_editor() as editor:
            editor.create_model(NFSe)
    tipo = TipoLoja.objects.create(nome=f"CRM {sufixo}", slug=f"tipo-{sufixo}", codigo=f"T{sufixo}"[:10].upper())
    plano = PlanoAssinatura.objects.create(
        nome=f"Plano {sufixo}", slug=f"plano-{sufixo}", descricao="teste", preco_mensal=Decimal("10.00"),
    )
    owner = User.objects.create_user(username=f"dono-{sufixo}", password="senha12345")
    loja = Loja.objects.create(
        nome=f"Loja {sufixo}", slug=f"loja-{sufixo}", tipo_loja=tipo, plano=plano, owner=owner,
    )
    set_current_loja_id(loja.id)
    set_current_tenant_db("default")
    return loja


class _LimpaContexto:
    def tearDown(self):
        from tenants.middleware import set_current_loja_id, set_current_tenant_db

        set_current_loja_id(None)
        set_current_tenant_db("default")
        super().tearDown()


class JanelaDaLojaTests(_LimpaContexto, TransactionTestCase):
    def test_nota_com_14_minutos_ainda_esta_saindo_e_nao_vira_erro(self):
        from nfse_integration.models import NFSe

        loja = _loja_com_tabela("janela-loja")
        saindo = NFSe.objects.create(
            loja_id=loja.id,
            numero_nf="PENDENTE-5",
            numero_rps=5,
            data_emissao=timezone.now() - timedelta(minutes=14),
            valor=Decimal("10.00"),
            tomador_cpf_cnpj="123",
            tomador_nome="Ana",
            servico_descricao="Consulta",
            status="pendente",
            provedor="nacional",
        )
        config = SimpleNamespace(provedor_nf="nacional", nacional_ultimo_dps=5, issnet_ultimo_rps_conhecido=0)
        dados = dict(
            tomador_cpf_cnpj="123",
            tomador_nome="Ana",
            tomador_email="",
            servico_descricao="Consulta",
            valor_servicos=Decimal("10.00"),
        )
        with self.assertRaises(EmissaoJaEmAndamento):
            reservar_emissao_loja(loja.id, config, **dados)
        saindo.refresh_from_db()
        self.assertEqual(saindo.status, "pendente")
        self.assertEqual(NFSe.objects.filter(loja_id=loja.id).count(), 1)

    def test_a_recusa_dentro_da_janela_avisa_que_esta_em_andamento(self):
        from nfse_integration.models import NFSe

        loja = _loja_com_tabela("janela-aviso")
        NFSe.objects.create(
            loja_id=loja.id,
            numero_nf="PENDENTE-6",
            numero_rps=6,
            data_emissao=timezone.now() - timedelta(minutes=14),
            valor=Decimal("10.00"),
            tomador_cpf_cnpj="123",
            tomador_nome="Ana",
            servico_descricao="Consulta",
            status="pendente",
            provedor="nacional",
        )
        config = SimpleNamespace(provedor_nf="nacional", nacional_ultimo_dps=6, issnet_ultimo_rps_conhecido=0)
        with self.assertRaises(EmissaoJaEmAndamento) as ctx:
            reservar_emissao_loja(
                loja.id, config,
                tomador_cpf_cnpj="123", tomador_nome="Ana", tomador_email="",
                servico_descricao="Consulta", valor_servicos=Decimal("10.00"),
            )
        self.assertIn("em andamento", str(ctx.exception))
        self.assertNotIn("passou do tempo", str(ctx.exception))


class JanelaDaLwkTests(TestCase):
    def test_nota_com_14_minutos_ainda_esta_saindo_e_nao_vira_erro(self):
        from asaas_integration.models_nfse_config import SuperadminNFSeConfig
        from superadmin.models import NFSeEmitida

        config = SuperadminNFSeConfig.get_config()
        config.nacional_ultimo_dps = 40
        config.ultimo_rps = 40
        config.save(update_fields=["nacional_ultimo_dps", "ultimo_rps", "updated_at"])
        saindo = NFSeEmitida.objects.create(
            numero_nf="PENDENTE-40",
            numero_rps=40,
            valor=Decimal("12.00"),
            tomador_cpf_cnpj="123",
            tomador_nome="Ana",
            descricao_servico="Consulta",
            status="pendente",
            provedor="nacional",
        )
        NFSeEmitida.objects.filter(pk=saindo.pk).update(created_at=timezone.now() - timedelta(minutes=14))
        payload = SimpleNamespace(
            loja=None, tomador_cpf_cnpj="123", tomador_nome="Ana", tomador_email="",
            descricao="Consulta", valor=Decimal("12.00"),
        )
        with self.assertRaises(RecusaLwk):
            reservar_emissao_superadmin(config, payload)
        saindo.refresh_from_db()
        self.assertEqual(saindo.status, "pendente")
        config.refresh_from_db()
        self.assertEqual(config.nacional_ultimo_dps, 40)
        self.assertEqual(NFSeEmitida.objects.count(), 1)


class RepeticaoDaFilaDaLojaTests(_LimpaContexto, TransactionTestCase):
    def _dados(self, numero):
        return {
            "tomador_cpf_cnpj": "123",
            "tomador_nome": "Ana",
            "servico_descricao": "Consulta",
            "valor_servicos": "10.00",
            "numero_rps_reservado": numero,
        }

    def test_dps_ja_emitido_devolve_a_nota_sem_chamar_a_prefeitura(self):
        from nfse_integration.loja_nfse_api import processar_emissao_nfse_loja_sync
        from nfse_integration.models import NFSe

        loja = _loja_com_tabela("fila-emitida")
        emitida = NFSe.objects.create(
            loja_id=loja.id,
            numero_nf="NF-777",
            numero_rps=7,
            data_emissao=timezone.now(),
            valor=Decimal("10.00"),
            tomador_cpf_cnpj="123",
            tomador_nome="Ana",
            servico_descricao="Consulta",
            status="emitida",
            provedor="nacional",
        )
        with patch("nfse_integration.service.NFSeService") as servico:
            servico.return_value.emitir_nfse.side_effect = _Chamou()
            corpo, http = processar_emissao_nfse_loja_sync(loja, loja.id, self._dados(7))
        self.assertEqual(http, 200)
        self.assertTrue(corpo["success"])
        self.assertEqual(corpo["nfse"]["id"], emitida.id)
        servico.return_value.emitir_nfse.assert_not_called()

    def test_dps_ainda_nao_emitido_segue_para_a_prefeitura(self):
        from nfse_integration.loja_nfse_api import processar_emissao_nfse_loja_sync

        loja = _loja_com_tabela("fila-nova")
        with patch("nfse_integration.service.NFSeService") as servico:
            servico.return_value.emitir_nfse.side_effect = _Chamou()
            with self.assertRaises(_Chamou):
                processar_emissao_nfse_loja_sync(loja, loja.id, self._dados(8))
        servico.return_value.emitir_nfse.assert_called_once()


class RepeticaoDaFilaDaLwkTests(TestCase):
    def _config(self):
        return SimpleNamespace(
            nacional_certificado=b"pfx",
            nacional_senha_certificado="enc",
            nacional_codigo_municipio="3543402",
            nacional_ambiente="homologacao",
            nacional_serie_dps="1",
            proximo_dps=MagicMock(side_effect=AssertionError("não devia gerar outro DPS")),
        )

    def _payload(self, numero):
        from nfse_integration.emissao_manual_types import EmissaoManualPayload

        return EmissaoManualPayload(
            loja=None, tomador_cpf_cnpj="123", tomador_nome="Ana", tomador_email="",
            tomador_endereco={}, valor=Decimal("12.00"), descricao="Consulta",
            codigo_cnae="", codigo_servico="", numero_dps_reservado=numero,
        )

    def test_dps_ja_emitido_devolve_a_nota_sem_chamar_a_prefeitura(self):
        from nfse_integration.emissao_nacional_superadmin import emitir_manual_nacional_superadmin
        from superadmin.models import NFSeEmitida

        emitida = NFSeEmitida.objects.create(
            numero_nf="NF-LWK-9",
            numero_rps=9,
            valor=Decimal("12.00"),
            tomador_cpf_cnpj="123",
            tomador_nome="Ana",
            descricao_servico="Consulta",
            status="emitida",
            provedor="nacional",
        )
        with patch("nfse_integration.nacional.NacionalClient", side_effect=_Chamou) as cliente:
            resultado = emitir_manual_nacional_superadmin(self._config(), self._payload(9))
        self.assertTrue(resultado.success)
        self.assertEqual(resultado.nfse_id, emitida.id)
        self.assertEqual(resultado.numero_nf, "NF-LWK-9")
        cliente.assert_not_called()

    def test_dps_ainda_nao_emitido_segue_para_a_prefeitura(self):
        from nfse_integration.emissao_nacional_superadmin import emitir_manual_nacional_superadmin

        with patch("nfse_integration.nacional.NacionalClient", side_effect=_Chamou), \
                patch("core.encryption.decrypt_value", return_value="senha"):
            with self.assertRaises(_Chamou):
                emitir_manual_nacional_superadmin(self._config(), self._payload(10))
