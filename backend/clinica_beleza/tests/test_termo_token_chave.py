"""Reenvio do termo não manda de novo um token que a chave atual não abre."""
from datetime import timedelta
from unittest.mock import MagicMock, patch
from urllib.parse import quote

from django.test import SimpleTestCase, override_settings

from clinica_beleza.consentimento_assinatura_adapter import ConsultaTermoAssinaturaAdapter
from clinica_beleza.consentimento_assinatura_envio_service import reenviar_termo_whatsapp
from clinica_beleza.views_assinatura_consentimento_internas import (
    ConsultaLinkAssinaturaProfissionalView,
)
from core.assinatura_service import gerar_token

CHAVE_ANTIGA = "chave-antiga-dos-links-de-assinatura-32"
CHAVE_NOVA = "chave-nova-depois-da-rotacao-secreta"


class _Arquivo:
    def __init__(self, linhas):
        self.linhas = linhas

    def select_related(self, *args):
        return self

    def filter(self, **kwargs):
        return self

    def order_by(self, *args):
        return self

    def first(self):
        return self.linhas[-1] if self.linhas else None

    def delete(self):
        self.linhas.clear()


def _termo():
    termo = MagicMock()
    termo.id = 7
    termo.consulta.patient.telefone = "11999999999"
    termo.consulta.patient.nome = "Ana"
    termo.status_assinatura_termo = "aguardando_profissional"
    termo.procedure.nome = "Limpeza"
    return termo


def _token(chave, *, expiracao=None):
    with override_settings(SECRET_KEY=chave):
        if expiracao is None:
            return gerar_token(
                "consultatermoprocedimento", 7, "paciente", 1, modulo="clinica_beleza",
            )
        return gerar_token(
            "consultatermoprocedimento", 7, "paciente", 1,
            modulo="clinica_beleza", expiracao=expiracao,
        )


def _linha(token):
    linha = MagicMock()
    linha.token = token
    linha.assinado = False
    return linha


class BuscarPendenteTest(SimpleTestCase):
    def test_mesma_chave_devolve_o_pendente(self):
        linha = _linha(_token(CHAVE_ANTIGA))
        arquivo = _Arquivo([linha])
        with override_settings(SECRET_KEY=CHAVE_ANTIGA), patch(
            "clinica_beleza.models.ConsultaAssinaturaTermo.objects", arquivo,
        ):
            achado = ConsultaTermoAssinaturaAdapter().buscar_assinatura_pendente(7, "paciente")
        self.assertIs(achado, linha)

    def test_outra_chave_nao_devolve_o_pendente(self):
        linha = _linha(_token(CHAVE_ANTIGA))
        arquivo = _Arquivo([linha])
        with override_settings(SECRET_KEY=CHAVE_NOVA), patch(
            "clinica_beleza.models.ConsultaAssinaturaTermo.objects", arquivo,
        ):
            achado = ConsultaTermoAssinaturaAdapter().buscar_assinatura_pendente(7, "paciente")
        self.assertIsNone(achado)
        self.assertEqual(arquivo.linhas, [linha])

    def test_token_vencido_nao_devolve_o_pendente(self):
        linha = _linha(_token(CHAVE_NOVA, expiracao=timedelta(seconds=-30)))
        arquivo = _Arquivo([linha])
        with override_settings(SECRET_KEY=CHAVE_NOVA), patch(
            "clinica_beleza.models.ConsultaAssinaturaTermo.objects", arquivo,
        ):
            achado = ConsultaTermoAssinaturaAdapter().buscar_assinatura_pendente(7, "paciente")
        self.assertIsNone(achado)


class ReenviarWhatsappTest(SimpleTestCase):
    def _reenviar(self, arquivo, chave):
        enviado = {}

        def enviar(*args, **kwargs):
            enviado["assinatura"] = args[2]
            return True, None

        def criar(adapter, documento, tipo, loja_id):
            novo = _linha(_token(chave))
            arquivo.linhas[:] = [novo]
            return novo

        termo = _termo()
        request = MagicMock()
        with (
            override_settings(SECRET_KEY=chave),
            patch("clinica_beleza.models.ConsultaAssinaturaTermo.objects", arquivo),
            patch("whatsapp.models.WhatsAppConfig.objects.filter", return_value=MagicMock(first=lambda: MagicMock())),
            patch("whatsapp.assinatura_whatsapp.whatsapp_envio_permitido", return_value=(True, None)),
            patch("whatsapp.assinatura_whatsapp.enviar_whatsapp_link_assinatura", side_effect=enviar),
            patch("core.assinatura_service.criar_assinatura", side_effect=criar),
        ):
            ok, telefone, err = reenviar_termo_whatsapp(
                termo_proc=termo,
                adapter=ConsultaTermoAssinaturaAdapter(),
                loja_id=1,
                request=request,
            )
        self.assertTrue(ok, err)
        self.assertEqual(telefone, "11999999999")
        return enviado["assinatura"]

    def test_outra_chave_gera_token_novo_e_apaga_o_antigo(self):
        antigo = _linha(_token(CHAVE_ANTIGA))
        arquivo = _Arquivo([antigo])
        enviado = self._reenviar(arquivo, CHAVE_NOVA)
        self.assertNotEqual(enviado.token, antigo.token)
        self.assertEqual(arquivo.linhas, [enviado])
        self.assertNotIn(antigo, arquivo.linhas)

    def test_mesma_chave_reaproveita_o_pendente(self):
        antigo = _linha(_token(CHAVE_NOVA))
        arquivo = _Arquivo([antigo])

        def criar(*args, **kwargs):
            raise AssertionError("não deve recriar")

        enviado = {}

        def enviar(*args, **kwargs):
            enviado["assinatura"] = args[2]
            return True, None

        termo = _termo()
        with (
            override_settings(SECRET_KEY=CHAVE_NOVA),
            patch("clinica_beleza.models.ConsultaAssinaturaTermo.objects", arquivo),
            patch("whatsapp.models.WhatsAppConfig.objects.filter", return_value=MagicMock(first=lambda: MagicMock())),
            patch("whatsapp.assinatura_whatsapp.whatsapp_envio_permitido", return_value=(True, None)),
            patch("whatsapp.assinatura_whatsapp.enviar_whatsapp_link_assinatura", side_effect=enviar),
            patch("core.assinatura_service.criar_assinatura", side_effect=criar),
        ):
            ok, _telefone, err = reenviar_termo_whatsapp(
                termo_proc=termo,
                adapter=ConsultaTermoAssinaturaAdapter(),
                loja_id=1,
                request=MagicMock(),
            )
        self.assertTrue(ok, err)
        self.assertIs(enviado["assinatura"], antigo)
        self.assertEqual(arquivo.linhas, [antigo])


class LinkProfissionalTest(SimpleTestCase):
    def _post(self, arquivo, chave):
        def criar(adapter, documento, tipo, loja_id):
            novo = _linha(_token(chave))
            arquivo.linhas[:] = [novo]
            return novo

        termo = _termo()
        view = ConsultaLinkAssinaturaProfissionalView()
        request = MagicMock()
        request.data = {"procedure_id": 3}
        with (
            override_settings(SECRET_KEY=chave),
            patch("clinica_beleza.models.ConsultaAssinaturaTermo.objects", arquivo),
            patch.object(view, "object_or_404", return_value=(MagicMock(), None)),
            patch(
                "clinica_beleza.views_assinatura_consentimento_internas.resolver_termo_procedimento",
                return_value=termo,
            ),
            patch("tenants.middleware.get_current_loja_id", return_value=1),
            patch("core.assinatura_service.criar_assinatura", side_effect=criar),
        ):
            response = view.post(request, pk=9)
        self.assertEqual(response.status_code, 200)
        return response.data["path"], arquivo

    def test_outra_chave_troca_o_caminho_do_profissional(self):
        antigo = _linha(_token(CHAVE_ANTIGA))
        path, arquivo = self._post(_Arquivo([antigo]), CHAVE_NOVA)
        self.assertNotIn(quote(antigo.token, safe=""), path)
        self.assertEqual(len(arquivo.linhas), 1)
        self.assertNotEqual(arquivo.linhas[0].token, antigo.token)
        self.assertIn(quote(arquivo.linhas[0].token, safe=""), path)

    def test_mesma_chave_reaproveita_o_caminho(self):
        antigo = _linha(_token(CHAVE_NOVA))
        arquivo = _Arquivo([antigo])

        def criar(*args, **kwargs):
            raise AssertionError("não deve recriar")

        termo = _termo()
        view = ConsultaLinkAssinaturaProfissionalView()
        request = MagicMock()
        request.data = {"procedure_id": 3}
        with (
            override_settings(SECRET_KEY=CHAVE_NOVA),
            patch("clinica_beleza.models.ConsultaAssinaturaTermo.objects", arquivo),
            patch.object(view, "object_or_404", return_value=(MagicMock(), None)),
            patch(
                "clinica_beleza.views_assinatura_consentimento_internas.resolver_termo_procedimento",
                return_value=termo,
            ),
            patch("tenants.middleware.get_current_loja_id", return_value=1),
            patch("core.assinatura_service.criar_assinatura", side_effect=criar),
        ):
            response = view.post(request, pk=9)
        self.assertEqual(response.status_code, 200)
        self.assertIn(quote(antigo.token, safe=""), response.data["path"])
        self.assertEqual(arquivo.linhas, [antigo])
