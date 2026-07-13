"""Emissão automática de NFS-e ao finalizar consulta com pagamento."""
from __future__ import annotations

import logging
import re
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)


def _get_nfse_config(loja_id: int):
    """Obtém configuração de NFS-e para a loja.
    Lê da tabela clinica_beleza_nfse_config (configuração individual da clínica).
    Fallback: tabela crm_vendas_crmconfig para lojas que ainda não migraram.
    """
    try:
        from django.db import connections
        conn = connections["default"]
        with conn.cursor() as c:
            c.execute("""
                SELECT emitir_nf_automaticamente, provedor_nf,
                       descricao_servico_padrao, codigo_servico_municipal,
                       item_lista_servico
                FROM clinica_beleza_nfse_config
                WHERE loja_id = %s
                LIMIT 1
            """, [loja_id])
            row = c.fetchone()
            if not row:
                # Fallback: tabela antiga (CRM) para retrocompatibilidade
                c.execute("""
                    SELECT emitir_nf_automaticamente, provedor_nf,
                           descricao_servico_padrao, codigo_servico_municipal,
                           item_lista_servico
                    FROM crm_vendas_crmconfig
                    WHERE loja_id = %s
                    LIMIT 1
                """, [loja_id])
                row = c.fetchone()
            if not row:
                return None

        class _NfseConfig:
            """Config de NFS-e lida diretamente do banco."""

            emitir_nf_automaticamente = row[0]
            provedor_nf = row[1] or "asaas"
            descricao_servico_padrao = row[2] or ""
            codigo_servico_municipal = row[3] or ""
            item_lista_servico = row[4] or ""

        return _NfseConfig()
    except Exception:
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

    provedor = (getattr(config, "provedor_nf", None) or "issnet").strip().lower()
    if provedor in ("manual", "desabilitado"):
        return

    validated_data = montar_payload_nfse_consulta(consulta, payment, config)
    if not validated_data:
        return

    if loja is None:
        from superadmin.models import Loja

        loja = Loja.objects.using("default").filter(id=loja_id).first()
    if not loja:
        logger.warning("NFS-e consulta %s: loja_id=%s não encontrada", consulta.id, loja_id)
        return

    from nfse_integration.loja_nfse_api import processar_emissao_nfse_loja_sync
    from nfse_integration.queue_dispatch import enqueue_emissao_nfse_loja, should_enqueue_nfse

    try:
        if should_enqueue_nfse():
            enqueue_emissao_nfse_loja(loja.id, validated_data)
            logger.info("NFS-e consulta %s enfileirada (loja %s)", consulta.id, loja.id)
            return
        processar_emissao_nfse_loja_sync(loja, loja.id, validated_data)
    except Exception:
        logger.exception("Falha ao emitir NFS-e da consulta %s", consulta.id)
