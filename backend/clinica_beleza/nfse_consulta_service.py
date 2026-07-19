"""Emissão automática de NFS-e ao finalizar consulta com pagamento."""
from __future__ import annotations

import logging
import re
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)


def _get_nfse_config(loja_id: int):
    """Obtém configuração de NFS-e da loja no schema tenant (não no public/default)."""
    try:
        from tenants.middleware import get_current_tenant_db

        from .models import ClinicaBelezaNFSeConfig

        db = get_current_tenant_db() or "default"
        config = (
            ClinicaBelezaNFSeConfig.objects.using(db)
            .filter(loja_id=loja_id)
            .only(
                "emitir_nf_automaticamente",
                "provedor_nf",
                "descricao_servico_padrao",
                "codigo_servico_municipal",
                "item_lista_servico",
            )
            .first()
        )
        if config is not None:
            return config
    except Exception:
        logger.debug("NFS-e config clinica_beleza indisponível loja_id=%s", loja_id, exc_info=True)

    # Fallback: tabela antiga (CRM) no mesmo tenant
    try:
        from django.db import connections
        from tenants.middleware import get_current_tenant_db

        db = get_current_tenant_db() or "default"
        conn = connections[db]
        with conn.cursor() as c:
            c.execute(
                """
                SELECT emitir_nf_automaticamente, provedor_nf,
                       descricao_servico_padrao, codigo_servico_municipal,
                       item_lista_servico
                FROM crm_vendas_crmconfig
                WHERE loja_id = %s
                LIMIT 1
                """,
                [loja_id],
            )
            row = c.fetchone()
        if not row:
            return None

        class _NfseConfig:
            emitir_nf_automaticamente = row[0]
            provedor_nf = row[1] or "asaas"
            descricao_servico_padrao = row[2] or ""
            codigo_servico_municipal = row[3] or ""
            item_lista_servico = row[4] or ""

        return _NfseConfig()
    except Exception:
        logger.debug("NFS-e config CRM fallback indisponível loja_id=%s", loja_id, exc_info=True)
        return None


def montar_payload_nfse_consulta(consulta, payment, config) -> dict[str, Any] | None:
    """Monta payload para emissão NFS-e a partir da consulta paga."""
    patient = consulta.patient
    cpf = re.sub(r"\D", "", getattr(patient, "cpf", "") or "")
    if len(cpf) < 11:
        logger.info(
            "NFS-e consulta %s: paciente sem CPF — emissão automática ignorada",
            consulta.id,
        )
        return None

    proc_name = None
    procedure = getattr(consulta, "procedure", None)
    if procedure is not None:
        proc_name = getattr(procedure, "nome", None) or getattr(procedure, "name", None)

    descricao = (getattr(config, "descricao_servico_padrao", "") or "").strip()
    if not descricao:
        descricao = "Serviços de estética, saúde e bem-estar"
    if proc_name:
        descricao = f"{descricao} — {proc_name}"

    endereco_text = (getattr(patient, "endereco", "") or "").strip()
    return {
        "tomador_cpf_cnpj": cpf,
        "tomador_nome": patient.nome,
        "tomador_email": (getattr(patient, "email", "") or "").strip(),
        "tomador_logradouro": endereco_text or "Não informado",
        "tomador_numero": "S/N",
        "tomador_bairro": "",
        "tomador_cidade": (getattr(patient, "cidade", "") or "").strip(),
        "tomador_uf": (getattr(patient, "estado", "") or "").strip(),
        "tomador_cep": "",
        "servico_descricao": descricao,
        "valor_servicos": payment.amount,
        "enviar_email": True,
        "codigo_servico": (getattr(config, "codigo_servico_municipal", "") or "").strip() or None,
        "item_lista_servico": (getattr(config, "item_lista_servico", "") or "").strip() or None,
    }


def _emitir_nfse_consulta_com_config(consulta, payment, config, *, loja=None) -> dict[str, Any]:
    """Emite NFS-e da consulta (manual ou automática). Retorna dict com success/queued/error."""
    provedor = (getattr(config, "provedor_nf", None) or "issnet").strip().lower()
    if provedor in ("manual", "desabilitado"):
        return {
            "success": False,
            "error": "Provedor de NFS-e está desabilitado ou em modo manual. Configure em Nota fiscal.",
        }

    validated_data = montar_payload_nfse_consulta(consulta, payment, config)
    if not validated_data:
        return {
            "success": False,
            "error": "Paciente sem CPF válido. Cadastre o CPF para emitir a nota.",
        }

    loja_id = getattr(consulta, "loja_id", None) or getattr(payment, "loja_id", None)
    if loja is None:
        from superadmin.models import Loja

        loja = Loja.objects.using("default").filter(id=loja_id).first()
    if not loja:
        return {"success": False, "error": "Loja não encontrada."}

    from nfse_integration.loja_nfse_api import processar_emissao_nfse_loja

    body, http_status = processar_emissao_nfse_loja(loja, loja.id, validated_data)
    ok = http_status in (200, 201, 202) and body.get("success", True) is not False
    if not ok:
        return {
            "success": False,
            "error": body.get("error") or body.get("message") or "Falha ao emitir NFS-e.",
            "detail": body,
        }
    logger.info("NFS-e consulta %s emitida/enfileirada (loja %s)", consulta.id, loja.id)
    return {
        "success": True,
        "queued": http_status == 202 or bool(body.get("queued")),
        "message": body.get("message") or "NFS-e emitida com sucesso.",
        "nfse": body.get("nfse") or body,
    }


def emitir_nfse_consulta_manual(consulta, payment, *, loja=None) -> dict[str, Any]:
    """Emissão manual de NFS-e a partir de consulta paga (ignora flag automática)."""
    if payment is None or getattr(payment, "status", "") != "PAID":
        return {"success": False, "error": "Só é possível emitir nota de consulta com pagamento quitado."}
    valor = getattr(payment, "amount", None)
    if valor is None or Decimal(str(valor)) <= 0:
        return {"success": False, "error": "Pagamento sem valor para emitir nota."}

    loja_id = getattr(consulta, "loja_id", None) or getattr(payment, "loja_id", None)
    if not loja_id:
        return {"success": False, "error": "Consulta sem loja."}

    config = _get_nfse_config(loja_id)
    if not config:
        return {
            "success": False,
            "error": "Configure a NFS-e em Configurações → Nota fiscal antes de emitir.",
        }

    try:
        return _emitir_nfse_consulta_com_config(consulta, payment, config, loja=loja)
    except Exception as exc:
        logger.exception("Falha ao emitir NFS-e manual da consulta %s", consulta.id)
        return {"success": False, "error": str(exc) or "Falha ao emitir NFS-e."}


def tentar_emitir_nfse_consulta(consulta, payment, *, loja=None) -> None:
    """Emite NFS-e após pagamento da consulta, se configurado.
    Falhas são registradas em log e não impedem a finalização.
    Usa config de NFS-e da loja (independente do app CRM).
    """
    if payment is None or getattr(payment, "status", "") != "PAID":
        return
    valor = getattr(payment, "amount", None)
    if valor is None or Decimal(str(valor)) <= 0:
        return

    loja_id = getattr(consulta, "loja_id", None) or getattr(payment, "loja_id", None)
    if not loja_id:
        return

    config = _get_nfse_config(loja_id)
    if not config:
        return
    if not getattr(config, "emitir_nf_automaticamente", False):
        return

    try:
        result = _emitir_nfse_consulta_com_config(consulta, payment, config, loja=loja)
        if not result.get("success"):
            logger.warning(
                "NFS-e automática consulta %s: %s",
                consulta.id,
                result.get("error"),
            )
    except Exception:
        logger.exception("Falha ao emitir NFS-e da consulta %s", consulta.id)
