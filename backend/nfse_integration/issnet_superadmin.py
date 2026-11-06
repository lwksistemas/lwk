"""ISSNet no contexto superadmin (NFSeEmitida). Cliente em issnet_client_factory."""
import logging
import re
from typing import Any

from django.utils import timezone

from nfse_integration.issnet_client_factory import (
    certificado_configurado as certificado_tem_bytes,
)
from nfse_integration.issnet_client_factory import (
    issnet_client_superadmin,
)
from nfse_integration.issnet_response import explicar_recusa_cancelamento
from nfse_integration.issnet_shared import CODIGOS_CANCELAMENTO, normalizar_codigo_cancelamento
from nfse_integration.issnet_status_sync import consultar_nfse_cancelada_issnet

logger = logging.getLogger(__name__)

__all__ = [
    "cancelar_nfse_emitida_superadmin",
    "certificado_configurado",
    "consultar_url_nfse_superadmin",
    "issnet_client_superadmin",
    "senha_certificado_configurada",
]


def certificado_configurado(config: Any) -> bool:
    return certificado_tem_bytes(config)


def senha_certificado_configurada(config: Any) -> bool:
    return bool(config.issnet_senha_certificado or config.nacional_senha_certificado)


def issnet_nacional_client_superadmin(config: Any):
    """Cliente ISSNet Nacional (DPS) com o certificado já gravado da LWK."""
    from core.encryption import decrypt_value

    from nfse_integration.certificado_armazenado import ler_pfx
    from nfse_integration.issnet_nacional_client import ISSNetNacionalClient

    cert = ler_pfx(bytes(config.issnet_certificado or config.nacional_certificado or b""))
    senha = decrypt_value(config.issnet_senha_certificado or config.nacional_senha_certificado or "")
    ambiente = (getattr(config, "nacional_ambiente", "") or "producao").strip()
    return ISSNetNacionalClient(
        cert_bytes=cert,
        cert_password=senha,
        ambiente=ambiente,
        prestador_cnpj=config.prestador_cnpj or "",
        prestador_inscricao_municipal=config.prestador_inscricao_municipal or "",
        optante_simples_nacional=bool(getattr(config, "optante_simples_nacional", True)),
    )


def _chave_acesso_emitida(nf: Any) -> str:
    chave = re.sub(r"\D", "", getattr(nf, "codigo_verificacao", "") or "")
    if len(chave) == 50:
        return chave
    xml = getattr(nf, "xml_nfse", "") or ""
    if not xml:
        return ""
    from nfse_integration.issnet_nacional_xml_builder import extrair_chave_acesso_nfse_nacional

    return re.sub(r"\D", "", extrair_chave_acesso_nfse_nacional(xml) or "")


def _emitida_no_padrao_nacional(nf: Any) -> bool:
    """Nota nova (DPS). Nota antiga do layout municipal continua no cancelamento ABRASF."""
    if len(_chave_acesso_emitida(nf)) == 50:
        return True
    return "sped.fazenda.gov.br/nfse" in (getattr(nf, "xml_nfse", "") or "")


def _cancelar_emitida_padrao_nacional(nf: Any, config: Any, codigo: str, motivo: str) -> dict[str, Any]:
    """Cancela NFS-e de assinatura no ISSNet padrão Nacional (evento da DPS)."""
    if not certificado_configurado(config):
        return {
            "success": False,
            "error": (
                "Certificado digital não configurado. "
                "Configure o certificado ISSNet para cancelar no portal da prefeitura."
            ),
        }
    try:
        client = issnet_nacional_client_superadmin(config)
        resultado = client.cancelar_nfse(
            numero_nfse=str(nf.numero_nf),
            motivo=motivo,
            codigo_cancelamento=codigo,
            chave_acesso=_chave_acesso_emitida(nf),
        )
        if resultado.get("success"):
            _marcar_cancelada(nf)
            return {
                "success": True,
                "message": f"NFS-e {nf.numero_nf} cancelada no ISSNet e no sistema.",
            }
        return {
            "success": False,
            "error": explicar_recusa_cancelamento(
                str(resultado.get("erro") or resultado.get("error") or "Erro desconhecido"),
            ),
        }
    except Exception as exc:
        logger.exception("Erro ao cancelar NFS-e superadmin via ISSNet Nacional: %s", exc)
        return {"success": False, "error": str(exc)}


def _marcar_cancelada(nf: Any) -> None:
    nf.status = "cancelada"
    nf.data_cancelamento = nf.data_cancelamento or timezone.now()
    nf.save(update_fields=["status", "data_cancelamento"])


def cancelar_nfse_emitida_superadmin(
    nf: Any,
    config: Any,
    codigo_cancelamento: str | int | None,
    motivo_texto: str,
) -> dict[str, Any]:
    """Cancela NFSeEmitida no ISSNet (quando aplicável) e atualiza status local."""
    codigo = normalizar_codigo_cancelamento(codigo_cancelamento)
    motivo_issnet = motivo_texto or CODIGOS_CANCELAMENTO[codigo]

    if nf.provedor == "issnet" and nf.numero_nf and _emitida_no_padrao_nacional(nf):
        return _cancelar_emitida_padrao_nacional(nf, config, codigo, motivo_issnet)

    if nf.provedor == "issnet" and nf.numero_nf:
        if not certificado_configurado(config):
            return {
                "success": False,
                "error": (
                    "Certificado digital não configurado. "
                    "Configure o certificado ISSNet para cancelar no portal da prefeitura."
                ),
            }

        cnpj = config.prestador_cnpj or ""
        im = config.prestador_inscricao_municipal or ""
        serie = (getattr(nf, "serie_rps", "") or "1").strip() or "1"
        numero_rps = int(nf.numero_rps) if getattr(nf, "numero_rps", 0) else None

        try:
            with issnet_client_superadmin(config) as client:
                resultado = client.cancelar_nfse(
                    numero_nf=nf.numero_nf,
                    motivo=motivo_issnet,
                    prestador_cnpj=cnpj,
                    inscricao_municipal=im,
                    codigo_cancelamento=codigo,
                )
                if resultado.get("success"):
                    _marcar_cancelada(nf)
                    return {
                        "success": True,
                        "message": f"NFS-e {nf.numero_nf} cancelada no ISSNet e no sistema.",
                    }

                if consultar_nfse_cancelada_issnet(
                    client,
                    numero_nf=str(nf.numero_nf),
                    numero_rps=numero_rps,
                    serie_rps=serie,
                    prestador_cnpj=cnpj,
                    inscricao_municipal=im,
                ):
                    _marcar_cancelada(nf)
                    return {
                        "success": True,
                        "message": (
                            f"NFS-e {nf.numero_nf} cancelada no ISSNet. "
                            "Status sincronizado com o portal."
                        ),
                    }

                return {
                    "success": False,
                    "error": explicar_recusa_cancelamento(
                        str(resultado.get("error") or "Erro desconhecido"),
                    ),
                }
        except Exception as exc:
            logger.exception("Erro ao cancelar NFS-e superadmin via ISSNet: %s", exc)
            return {"success": False, "error": str(exc)}

    if nf.provedor == "nacional":
        from nfse_integration.nacional.cancelamento import cancelar_nfse_sefin
        from nfse_integration.numero_exibicao import numero_nfse_para_exibicao

        resultado = cancelar_nfse_sefin(nf, config, codigo, motivo_issnet)
        if not resultado.get("success"):
            return {"success": False, "error": resultado.get("error") or "Erro ao cancelar na Sefin"}
        _marcar_cancelada(nf)
        numero = numero_nfse_para_exibicao(nf) or nf.numero_nf
        return {
            "success": True,
            "message": f"NFS-e {numero} cancelada no Emissor Nacional e no sistema.",
        }

    return {
        "success": False,
        "error": f"Cancelamento automático não disponível para o provedor «{nf.provedor}».",
    }


def consultar_url_nfse_superadmin(nf: Any, config: Any) -> dict[str, Any]:
    """Chama ConsultarUrlNfse no ISSNet (diagnóstico superadmin)."""
    with issnet_client_superadmin(config, prefix="issnet_dbg_") as client:
        return client.consultar_url_nfse(
            numero_nf=nf.numero_nf,
            prestador_cnpj=config.prestador_cnpj or "",
            inscricao_municipal=config.prestador_inscricao_municipal or "",
        )
