"""Consulta de status de cancelamento no ISSNet (RPS + fallback URL do portal)."""
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _erro_permite_fallback_url(erro: str) -> bool:
    err = (erro or "").upper()
    return "E160" in err or "E183" in err or "XML SCHEMA" in err


def consultar_nfse_cancelada_issnet(
    client: Any,
    *,
    numero_nf: str,
    numero_rps: int | None,
    serie_rps: str,
    prestador_cnpj: str,
    inscricao_municipal: str,
) -> bool:
    """Retorna True se o ISSNet indica que a NFS-e está cancelada.
    Tenta ConsultarNfsePorRps; em falha de schema, usa URL do portal.
    """
    out: dict[str, Any] = {}
    if numero_rps:
        try:
            out = client.consultar_nfse_por_rps(
                numero_rps=int(numero_rps),
                serie_rps=str(serie_rps or "1"),
                prestador_cnpj=str(prestador_cnpj or ""),
                inscricao_municipal=str(inscricao_municipal or ""),
            )
        except Exception as exc:
            logger.warning("Consulta RPS ISSNet falhou: %s", exc)
            out = {"success": False, "error": str(exc)}

        if out.get("cancelada"):
            return True
        if out.get("success") is not False:
            return False

    if not numero_nf:
        return False

    err = str(out.get("error") or "")
    if numero_rps and not _erro_permite_fallback_url(err):
        return False

    try:
        url_out = client.consultar_url_nfse(
            numero_nf=str(numero_nf),
            prestador_cnpj=str(prestador_cnpj or ""),
            inscricao_municipal=str(inscricao_municipal or ""),
        )
        if url_out.get("success") and url_out.get("url"):
            inf = client.inferir_cancelada_por_url(url=str(url_out["url"]))
            return bool(inf.get("success") and inf.get("cancelada"))
    except Exception as exc:
        logger.warning("Fallback URL ISSNet falhou: %s", exc)

    return False
