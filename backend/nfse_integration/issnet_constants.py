"""Constantes ISSNet Ribeirão Preto (ABRASF 2.04 + Nacional)."""

NS_NFSE = "http://www.abrasf.org.br/nfse.xsd"
NS_NFSE_WSDL = "http://nfse.abrasf.org.br"
NS_NFSE_NACIONAL = "http://www.sped.fazenda.gov.br/nfse"
COD_MUNICIPIO_RP = "3543402"

# === Endpoints ABRASF (legado — será descontinuado 03/08/2026) ===
ISSNET_RP_NFSE_ASMX = (
    "https://nfse.issnetonline.com.br/abrasf204/ribeiraopreto/nfse.asmx"
)

# === Endpoints Nacional (novo padrão RTC) ===
ISSNET_RP_NACIONAL_PRODUCAO = (
    "https://nfse.issnetonline.com.br/wsnfsenacional/ribeiraopreto/nfse.asmx"
)
ISSNET_RP_NACIONAL_HOMOLOG = (
    "https://nfse.issnetonline.com.br/wsnfsenacional/homologacao/nfse.asmx"
)

# URLs agrupadas
ISSNET_RP_NFSE_HOMOLOG = ISSNET_RP_NACIONAL_HOMOLOG

ISSNET_URLS = {
    "producao": ISSNET_RP_NFSE_ASMX,
    "homologacao": ISSNET_RP_NFSE_HOMOLOG,
}

ISSNET_NACIONAL_URLS = {
    "producao": ISSNET_RP_NACIONAL_PRODUCAO,
    "homologacao": ISSNET_RP_NACIONAL_HOMOLOG,
}

# === SOAP Actions ABRASF (legado) ===
SOAP_ACTION_RECEPCIONAR_LOTE_RPS = "http://nfse.abrasf.org.br/RecepcionarLoteRps"
SOAP_ACTION_RECEPCIONAR_LOTE_RPS_SINCRONO = (
    "http://nfse.abrasf.org.br/RecepcionarLoteRpsSincrono"
)
SOAP_ACTION_CONSULTAR_LOTE_RPS = "http://nfse.abrasf.org.br/ConsultarLoteRps"

# === SOAP Actions Nacional (ISSNet wsnfsenacional / NotaControl) ===
# ACBr e o WSDL Nacional usam o namespace SPED — NÃO abrasf.org.br.
SOAP_ACTION_NACIONAL_RECEPCIONAR_LOTE_DPS = (
    f"{NS_NFSE_NACIONAL}/RecepcionarLoteDps"
)
SOAP_ACTION_NACIONAL_RECEPCIONAR_LOTE_DPS_SINCRONO = (
    f"{NS_NFSE_NACIONAL}/RecepcionarLoteDpsSincrono"
)
SOAP_ACTION_NACIONAL_CANCELAR_NFSE = (
    f"{NS_NFSE_NACIONAL}/CancelarNfse"
)
SOAP_ACTION_NACIONAL_CONSULTAR_NFSE_DPS = (
    f"{NS_NFSE_NACIONAL}/ConsultarNfseDps"
)
SOAP_ACTION_NACIONAL_CONSULTAR_URL_NFSE = (
    f"{NS_NFSE_NACIONAL}/ConsultarUrlNfse"
)

# === Cabeçalhos SOAP ===
CABEC_MSG = (
    '<cabecalho versao="2.04" xmlns="http://www.abrasf.org.br/nfse.xsd">'
    '<versaoDados>2.04</versaoDados>'
    '</cabecalho>'
)

CABEC_MSG_NACIONAL = (
    '<cabecalho versao="1.01" xmlns="http://www.sped.fazenda.gov.br/nfse">'
    '<versaoDados>1.01</versaoDados>'
    '</cabecalho>'
)
