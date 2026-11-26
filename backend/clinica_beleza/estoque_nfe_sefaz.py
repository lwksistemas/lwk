"""NF-e na SEFAZ (implementação em core.nfe.sefaz)."""
from core.nfe.sefaz import *  # noqa: F401,F403
from core.nfe.sefaz import (  # noqa: F401
    CIENCIA,
    CSTAT_CONSUMO,
    CSTAT_DOCUMENTOS,
    CSTAT_EVENTO_OK,
    CSTAT_VAZIO,
    NS_NFE,
    UF_IBGE,
    URL_DIST,
    URL_EVENTO,
    SefazNfeErro,
    classificar_documento,
    codigo_uf,
    consultar_distribuicao,
    enviar_ciencia,
    interpretar_ret_dist,
    pem_do_pfx,
    postar_soap,
    xml_evento_ciencia,
)
