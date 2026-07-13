"""Constantes ISSNet Ribeirão Preto (ABRASF 2.04)."""

NS_NFSE = "http://www.abrasf.org.br/nfse.xsd"
NS_NFSE_WSDL = "http://nfse.abrasf.org.br"
COD_MUNICIPIO_RP = "3543402"

ISSNET_RP_NFSE_ASMX = (
    "https://nfse.issnetonline.com.br/abrasf204/ribeiraopreto/nfse.asmx"
)
ISSNET_RP_NFSE_HOMOLOG = (
    "https://nfse.issnetonline.com.br/wsnfsenacional/homologacao/nfse.asmx"
)

SOAP_ACTION_RECEPCIONAR_LOTE_RPS = "http://nfse.abrasf.org.br/RecepcionarLoteRps"
SOAP_ACTION_RECEPCIONAR_LOTE_RPS_SINCRONO = (
    "http://nfse.abrasf.org.br/RecepcionarLoteRpsSincrono"
)
SOAP_ACTION_CONSULTAR_LOTE_RPS = "http://nfse.abrasf.org.br/ConsultarLoteRps"

ISSNET_URLS = {
    "producao": ISSNET_RP_NFSE_ASMX,
    "homologacao": ISSNET_RP_NFSE_HOMOLOG,
}

CABEC_MSG = (
    '<cabecalho versao="2.04" xmlns="http://www.abrasf.org.br/nfse.xsd">'
    '<versaoDados>2.04</versaoDados>'
    '</cabecalho>'
)
