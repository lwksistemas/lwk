"""Enfileira emissões NFS-e no lwks-backend (django-q + Redis)."""
from __future__ import annotations

from typing import Any

from nfse_integration.queue_serialize import payload_emissao_manual_to_dict, serialize_validated_data


def should_enqueue_nfse() -> bool:
    from core.task_queue import task_queue_enabled
    from nfse_integration.sync_context import nfse_sync_only

    return task_queue_enabled() and not nfse_sync_only.get()


def enqueue_emitir_nfse_assinatura(pagamento, payment_id: str = "") -> bool:
    from core.task_queue import enqueue_task

    if not pagamento:
        return False
    enqueue_task(
        f"nfse-assinatura-{pagamento.id}",
        "nfse_integration.queue_tasks.run_emitir_nfse_assinatura",
        pagamento.id,
        payment_id or "",
    )
    return True


def enqueue_emissao_nfse_loja(loja_id: int, validated_data: dict[str, Any]) -> bool:
    from core.task_queue import enqueue_task

    payload = serialize_validated_data(validated_data)
    key = abs(hash((loja_id, payload.get("servico_descricao", ""), payload.get("valor_servicos", ""))))
    enqueue_task(
        f"nfse-loja-{loja_id}-{key}",
        "nfse_integration.queue_tasks.run_emissao_nfse_loja",
        loja_id,
        payload,
    )
    return True


def enqueue_emitir_nfse_manual(payload) -> bool:
    from core.task_queue import enqueue_task

    data = payload_emissao_manual_to_dict(payload)
    enqueue_task(
        f'nfse-manual-{data.get("loja_id") or "ext"}-{hash(data.get("tomador_cpf_cnpj", ""))}',
        "nfse_integration.queue_tasks.run_emitir_nfse_manual",
        data,
    )
    return True


def enqueue_emitir_nfse_comissao(relatorio_id: int, loja_id: int) -> bool:
    from core.task_queue import enqueue_task

    enqueue_task(
        f"nfse-comissao-{loja_id}-{relatorio_id}",
        "nfse_integration.queue_tasks.run_emitir_nfse_comissao",
        relatorio_id,
        loja_id,
    )
    return True
