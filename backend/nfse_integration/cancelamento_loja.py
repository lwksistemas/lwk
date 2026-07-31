"""Cancelamento de NFS-e no contexto da loja (CRM)."""
import contextlib
import logging
import re
from typing import Any

from django.utils import timezone

from nfse_integration.email_nfse import notificar_cancelamento_nfse
from nfse_integration.issnet_loja import certificado_configurado_loja, issnet_client_loja
from nfse_integration.issnet_nacional_client import ISSNetNacionalClient
from nfse_integration.issnet_shared import CODIGOS_CANCELAMENTO, normalizar_codigo_cancelamento
from nfse_integration.issnet_status_sync import consultar_nfse_cancelada_issnet

logger = logging.getLogger(__name__)


def _marcar_cancelada_loja(nfse: Any) -> None:
    nfse.status = "cancelada"
    nfse.data_cancelamento = timezone.now()
    nfse.save(update_fields=["status", "data_cancelamento", "updated_at"])


def _provedor_efetivo(nfse: Any, config: Any) -> str:
    nf_prov = (getattr(nfse, "provedor", "") or "").strip().lower()
    cfg_prov = (getattr(config, "provedor_nf", "") or "").strip().lower()
    return nf_prov or cfg_prov


def _usar_nacional_cancelamento(config: Any) -> bool:
    """Usa ISSNet Nacional (DPS/RTC) para cancelamento quando a configuração ativa o padrão
    ou a partir de 31/07/2026, quando o ABRASF legado deixa de ser aceito em Ribeirão Preto."""
    from datetime import date

    if bool(getattr(config, "issnet_usar_padrao_nacional", False)):
        return True
    return date.today() >= date(2026, 7, 31)


def _criar_client_nacional_cancelamento(
    config: Any,
    cnpj_prestador: str,
    im_prestador: str,
) -> ISSNetNacionalClient:
    """Cria ISSNetNacionalClient a partir da config da loja para cancelamento."""
    from core.encryption import decrypt_value

    cert_bytes = getattr(config, "issnet_certificado", None) or getattr(config, "nacional_certificado", None)
    if not cert_bytes:
        raise ValueError("Certificado digital não configurado.")

    senha = getattr(config, "issnet_senha_certificado", "") or getattr(config, "nacional_senha_certificado", "") or ""
    if senha and callable(decrypt_value):
        with contextlib.suppress(Exception):
            senha = decrypt_value(senha)

    ambiente = "homologacao" if getattr(config, "issnet_ambiente_homologacao", False) else "producao"

    return ISSNetNacionalClient(
        cert_bytes=bytes(cert_bytes),
        cert_password=senha,
        ambiente=ambiente,
        prestador_cnpj=cnpj_prestador,
        prestador_inscricao_municipal=im_prestador,
        optante_simples_nacional=bool(getattr(config, "optante_simples_nacional", True)),
    )


def _cancelar_nfse_loja_nacional(
    *,
    loja: Any,
    config: Any,
    nfse: Any,
    numero_nf: str,
    motivo: str,
    codigo_cancelamento: str,
    cnpj_prestador: str,
    im_prestador: str,
) -> dict[str, Any]:
    """Cancela NFS-e via ISSNet padrão Nacional (DPS/RTC)."""
    try:
        client = _criar_client_nacional_cancelamento(config, cnpj_prestador, im_prestador)
        chave_acesso = getattr(nfse, "codigo_verificacao", "") or getattr(nfse, "chave_acesso", "") or ""
        resultado = client.cancelar_nfse(
            numero_nfse=str(numero_nf),
            motivo=motivo,
            codigo_cancelamento=codigo_cancelamento,
            chave_acesso=str(chave_acesso),
        )
        if resultado.get("success"):
            _marcar_cancelada_loja(nfse)
            try:
                notificar_cancelamento_nfse(
                    nfse=nfse,
                    loja=loja,
                    loja_id=getattr(loja, "id", None),
                    config=config,
                )
            except Exception as exc:
                logger.warning("Falha ao enviar email de cancelamento: %s", exc)
            return {"success": True, "message": "NFS-e cancelada com sucesso no ISSNet Nacional."}

        return {
            "success": False,
            "error": resultado.get("erro", "Erro ao cancelar no ISSNet Nacional"),
        }
    except Exception as exc:
        logger.exception("Erro ao cancelar NFS-e via ISSNet Nacional: %s", exc)
        return {"success": False, "error": str(exc)}


def cancelar_nfse_loja(
    loja: Any,
    config: Any,
    nfse: Any,
    numero_nf: str,
    motivo: str,
    codigo_cancelamento: str | int | None = "1",
) -> dict[str, Any]:
    """Cancela NFS-e no ISSNet e só então atualiza o status local.
    Nunca marca como cancelada sem confirmação do portal.
    """
    if not nfse.pode_cancelar():
        return {"success": False, "error": "Esta NFS-e não pode ser cancelada"}

    provedor = _provedor_efetivo(nfse, config)

    if provedor == "asaas":
        return {
            "success": False,
            "error": "NFS-e emitida via Asaas: cancele no painel Asaas e use «Sincronizar».",
        }

    if provedor == "manual":
        return {
            "success": False,
            "error": "NFS-e manual: cancele no portal da prefeitura e use «Sincronizar».",
        }

    if provedor == "nacional":
        return {
            "success": False,
            "error": (
                "Cancelamento via API Nacional ainda não disponível. "
                "Cancele no portal da prefeitura e use «Sincronizar»."
            ),
        }

    if provedor != "issnet":
        return {
            "success": False,
            "error": f"Cancelamento automático não disponível para o provedor «{provedor}».",
        }

    if not numero_nf or str(numero_nf).startswith("FALHA-"):
        return {
            "success": False,
            "error": "NFS-e sem número válido para cancelamento no portal ISSNet.",
        }

    if not certificado_configurado_loja(config):
        return {
            "success": False,
            "error": (
                "Certificado digital não configurado. "
                "Configure o certificado ISSNet para cancelar no portal da prefeitura."
            ),
        }

    codigo = normalizar_codigo_cancelamento(codigo_cancelamento)
    motivo_final = motivo or CODIGOS_CANCELAMENTO[codigo]

    cnpj_prestador = re.sub(r"\D", "", loja.cpf_cnpj or "")
    im_prestador = (
        getattr(config, "inscricao_municipal", "")
        or getattr(loja, "inscricao_municipal", "")
        or ""
    )
    serie = getattr(config, "issnet_serie_rps", "1") or "1"
    numero_rps = int(nfse.numero_rps) if nfse.numero_rps else None

    if _usar_nacional_cancelamento(config):
        return _cancelar_nfse_loja_nacional(
            loja=loja,
            config=config,
            nfse=nfse,
            numero_nf=numero_nf,
            motivo=motivo_final,
            codigo_cancelamento=codigo,
            cnpj_prestador=cnpj_prestador,
            im_prestador=im_prestador,
        )

    try:
        with issnet_client_loja(config) as client:
            resultado = client.cancelar_nfse(
                numero_nf=numero_nf,
                motivo=motivo_final,
                prestador_cnpj=cnpj_prestador,
                inscricao_municipal=im_prestador,
                codigo_cancelamento=codigo,
            )
            if resultado.get("success"):
                _marcar_cancelada_loja(nfse)
                try:
                    notificar_cancelamento_nfse(
                        nfse=nfse,
                        loja=loja,
                        loja_id=getattr(loja, "id", None),
                        config=config,
                    )
                except Exception as exc:
                    logger.warning("Falha ao enviar email de cancelamento: %s", exc)
                return {"success": True, "message": "NFS-e cancelada com sucesso no ISSNet."}

            if consultar_nfse_cancelada_issnet(
                client,
                numero_nf=str(numero_nf),
                numero_rps=numero_rps,
                serie_rps=str(serie),
                prestador_cnpj=cnpj_prestador,
                inscricao_municipal=im_prestador,
            ):
                _marcar_cancelada_loja(nfse)
                try:
                    notificar_cancelamento_nfse(
                        nfse=nfse,
                        loja=loja,
                        loja_id=getattr(loja, "id", None),
                        config=config,
                    )
                except Exception as exc:
                    logger.warning("Falha ao enviar email de cancelamento: %s", exc)
                return {
                    "success": True,
                    "message": (
                        "NFS-e já constava cancelada no ISSNet. "
                        "O status foi sincronizado com o portal."
                    ),
                }

        return {
            "success": False,
            "error": resultado.get("error", "Erro ao cancelar no ISSNet"),
        }
    except Exception as exc:
        logger.exception("Erro ao cancelar NFS-e via ISSNet: %s", exc)
        return {"success": False, "error": str(exc)}
