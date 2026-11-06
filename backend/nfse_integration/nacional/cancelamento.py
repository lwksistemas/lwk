"""Cancelamento de NFS-e no Emissor Nacional (evento e101101 da Sefin)."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from lxml import etree

from nfse_integration.issnet_nacional_xml_builder import _motivo_cancelamento_nacional
from nfse_integration.nacional.constants import NS_NFSE
from nfse_integration.numero_exibicao import chave_acesso_nfse

logger = logging.getLogger(__name__)

_FUSO = ZoneInfo("America/Sao_Paulo")
_DESC_CANCELAMENTO = "Cancelamento de NFS-e"


def _digitos(valor: str) -> str:
    return "".join(c for c in (valor or "") if c.isdigit())


def construir_xml_cancelamento_sefin(
    *,
    chave_acesso: str,
    prestador_cnpj: str,
    codigo_cancelamento: str,
    motivo: str,
    ambiente: str = "producao",
    dh_evento: datetime | None = None,
) -> str:
    """Pedido de registro do evento e101101. A Sefin cancela direto; não pede análise fiscal."""
    chave = _digitos(chave_acesso)
    doc = _digitos(prestador_cnpj)
    c_motivo, x_motivo = _motivo_cancelamento_nacional(codigo_cancelamento, motivo)
    quando = dh_evento or datetime.now(_FUSO)
    if quando.tzinfo is None:
        quando = quando.replace(tzinfo=_FUSO)
    id_ped = f"PRE{chave}101101001"

    root = etree.Element(f"{{{NS_NFSE}}}pedRegEvento", versao="1.01", nsmap={None: NS_NFSE})
    inf = etree.SubElement(root, f"{{{NS_NFSE}}}infPedReg", Id=id_ped)
    etree.SubElement(inf, f"{{{NS_NFSE}}}tpAmb").text = "2" if ambiente == "homologacao" else "1"
    etree.SubElement(inf, f"{{{NS_NFSE}}}verAplic").text = "LWKSistemas"
    etree.SubElement(inf, f"{{{NS_NFSE}}}dhEvento").text = quando.isoformat(timespec="seconds")
    etree.SubElement(inf, f"{{{NS_NFSE}}}{'CPFAutor' if len(doc) == 11 else 'CNPJAutor'}").text = doc
    etree.SubElement(inf, f"{{{NS_NFSE}}}chNFSe").text = chave
    etree.SubElement(inf, f"{{{NS_NFSE}}}nPedRegEvento").text = "1"
    evento = etree.SubElement(inf, f"{{{NS_NFSE}}}e101101")
    etree.SubElement(evento, f"{{{NS_NFSE}}}xDesc").text = _DESC_CANCELAMENTO
    etree.SubElement(evento, f"{{{NS_NFSE}}}cMotivo").text = c_motivo
    etree.SubElement(evento, f"{{{NS_NFSE}}}xMotivo").text = x_motivo
    return etree.tostring(root, encoding="unicode")


def cancelar_nfse_sefin(nf: Any, config: Any, codigo: str, motivo: str) -> dict[str, Any]:
    """Envia o cancelamento à Sefin e devolve success/error. Não altera o banco."""
    from nfse_integration.nacional.transport import (
        comprimir_e_codificar,
        enviar_evento_sefin,
        interpretar_resposta_evento,
    )
    from nfse_integration.nacional.xml_signer import assinar_xml_dps_bytes

    if not getattr(config, "nacional_certificado", None) or not getattr(config, "nacional_senha_certificado", None):
        return {"success": False, "error": "Certificado digital Nacional não configurado"}

    chave = chave_acesso_nfse(nf)
    if len(chave) != 50:
        return {"success": False, "error": "A nota nacional não tem chave de acesso para cancelar"}

    xml = construir_xml_cancelamento_sefin(
        chave_acesso=chave,
        prestador_cnpj=getattr(config, "prestador_cnpj", "") or "",
        codigo_cancelamento=codigo,
        motivo=motivo,
        ambiente=getattr(config, "nacional_ambiente", None) or "producao",
    )
    assinado = assinar_xml_dps_bytes(
        xml,
        bytes(config.nacional_certificado),
        config.nacional_senha_certificado,
        prefixo_ds=False,
        usar_cadeia=False,
        usar_sha256=True,
        elemento="infPedReg",
    )
    resposta = enviar_evento_sefin(
        comprimir_e_codificar(assinado),
        chave,
        ambiente=getattr(config, "nacional_ambiente", None) or "producao",
        pfx_bytes=bytes(config.nacional_certificado),
        senha_pfx=config.nacional_senha_certificado,
    )
    dados = resposta.get("data") if isinstance(resposta.get("data"), dict) else {}
    lido = interpretar_resposta_evento(dados)
    if resposta.get("success") and lido.get("success"):
        logger.info("NFS-e nacional cancelada na Sefin: rps=%s", getattr(nf, "numero_rps", ""))
        return {"success": True, "xml_evento": lido.get("xml_evento") or ""}
    erro = lido.get("error") or resposta.get("error") or "Sefin Nacional rejeitou o cancelamento"
    logger.warning("Cancelamento nacional recusado: %s", str(erro)[:300])
    return {"success": False, "error": erro}
