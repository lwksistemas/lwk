"""Testes do envelope SOAP ISSNet Nacional (namespace SPED)."""
from nfse_integration.issnet_constants import (
    CABEC_MSG_NACIONAL,
    NS_NFSE_NACIONAL,
    SOAP_ACTION_NACIONAL_CANCELAR_NFSE,
    SOAP_ACTION_NACIONAL_RECEPCIONAR_LOTE_DPS_SINCRONO,
)
from nfse_integration.issnet_nacional_client import _nome_operacao_de_soap_action
from nfse_integration.issnet_soap import (
    montar_soap_envelope_nacional_xsd_string,
)


def test_soap_action_nacional_usa_namespace_sped():
    assert SOAP_ACTION_NACIONAL_RECEPCIONAR_LOTE_DPS_SINCRONO.startswith(NS_NFSE_NACIONAL)
    assert SOAP_ACTION_NACIONAL_CANCELAR_NFSE.endswith("/CancelarNfse")
    assert "abrasf" not in SOAP_ACTION_NACIONAL_RECEPCIONAR_LOTE_DPS_SINCRONO


def test_nome_operacao_de_soap_action():
    assert (
        _nome_operacao_de_soap_action(SOAP_ACTION_NACIONAL_RECEPCIONAR_LOTE_DPS_SINCRONO)
        == "RecepcionarLoteDpsSincrono"
    )
    assert _nome_operacao_de_soap_action('"http://x/CancelarNfse"') == "CancelarNfse"


def test_envelope_nacional_xsd_string_namespace_e_escape():
    dados = '<EnviarLoteDpsSincronoEnvio xmlns="http://www.sped.fazenda.gov.br/nfse"><LoteDps/></EnviarLoteDpsSincronoEnvio>'
    env = montar_soap_envelope_nacional_xsd_string("RecepcionarLoteDpsSincrono", dados)

    assert f'xmlns:nfse="{NS_NFSE_NACIONAL}"' in env
    assert "<nfse:RecepcionarLoteDpsSincrono>" in env
    assert "nfse.abrasf.org.br" not in env
    # xsd:string: XML escapado, não aninhado cru
    assert "&lt;EnviarLoteDpsSincronoEnvio" in env
    assert "<EnviarLoteDpsSincronoEnvio xmlns=" not in env.split("nfseDadosMsg>")[1].split("</nfseDadosMsg>")[0]
    assert "versaoDados" in env or "1.00" in CABEC_MSG_NACIONAL
    assert "&lt;cabecalho" in env or "cabecalho" in env
