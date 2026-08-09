"""Testes de extração de chave e XML anexo (ISSNet Nacional)."""
from nfse_integration.issnet_nacional_xml_builder import (
    extrair_chave_acesso_nfse_nacional,
    xml_nfse_para_anexo_email,
)
from nfse_integration.issnet_shared import (
    ISSNET_NACIONAL_OBRIGATORIO_DESDE,
    usar_issnet_padrao_nacional,
)

CHAVE_50 = "35434021234567890123456789012345678901234567890123"
assert len(CHAVE_50) == 50


SAMPLE_GERARNFSE = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <GerarNfseResponse xmlns="http://www.sped.fazenda.gov.br/nfse">
      <GerarNfseResposta>
        <ListaNfse>
          <CompNfse>
            <NFSe>
              <infNFSe Id="NFS{CHAVE_50}">
                <nNFSe>123</nNFSe>
              </infNFSe>
            </NFSe>
          </CompNfse>
        </ListaNfse>
      </GerarNfseResposta>
    </GerarNfseResponse>
  </soap:Body>
</soap:Envelope>
"""


def test_extrair_chave_do_id_inf_nfse():
    assert extrair_chave_acesso_nfse_nacional(SAMPLE_GERARNFSE) == CHAVE_50


def test_extrair_chave_tag_explicita():
    xml = f"<root><ChaveAcesso>{CHAVE_50}</ChaveAcesso></root>"
    assert extrair_chave_acesso_nfse_nacional(xml) == CHAVE_50


def test_extrair_chave_vazia():
    assert extrair_chave_acesso_nfse_nacional("") is None
    assert extrair_chave_acesso_nfse_nacional("<root/>") is None


def test_xml_anexo_remove_soap():
    anexo = xml_nfse_para_anexo_email(SAMPLE_GERARNFSE)
    assert "soap:Envelope" not in anexo
    assert "CompNfse" in anexo or "NFSe" in anexo
    assert f'Id="NFS{CHAVE_50}"' in anexo


def test_usar_issnet_padrao_nacional_flag():
    class Cfg:
        issnet_usar_padrao_nacional = True

    assert usar_issnet_padrao_nacional(Cfg()) is True


def test_usar_issnet_padrao_nacional_data_corte():
    class Cfg:
        issnet_usar_padrao_nacional = False

    # Hoje (ago/2026) >= corte → True
    assert ISSNET_NACIONAL_OBRIGATORIO_DESDE.year == 2026
    assert usar_issnet_padrao_nacional(Cfg()) is True
    assert usar_issnet_padrao_nacional(None) is False
