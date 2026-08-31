"""Gateway WhatsApp para sistemas PHP: Evolution de parceiro, isolada das lojas.

Enquanto EVOLUTION_PARCEIRO_* estiver vazio, o gateway recusa números.
Não usar a Evolution das lojas (EVOLUTION_API_*).
"""
from __future__ import annotations

import logging
import re
from urllib.parse import urlparse

import requests
from django.utils import timezone

from superadmin.models import WhatsappCustomer, WhatsappInstance
from whatsapp.evolution_client import (
    EvolutionAPIError,
    _extract_pairing_code,
    _extract_qr_base64,
    _normalize_evolution_state,
    create_evolution_instance_with_qr,
    evolution_target,
    get_connection_state,
    logout_instance,
    partner_evolution_configured,
    send_text,
    set_instance_webhook,
)

logger = logging.getLogger(__name__)


def nome_instancia_parceiro(customer_id: int, cliente_id: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", (cliente_id or "").strip())[:40].strip("_").lower()
    slug = slug or "n"
    return f"ext_{int(customer_id)}_{slug}"[:80]


def instancia_do_parceiro(customer: WhatsappCustomer, instance_name: str) -> WhatsappInstance | None:
    name = (instance_name or "").strip()
    prefix = f"ext_{customer.id}_"
    if not name.startswith(prefix):
        return None
    return WhatsappInstance.objects.filter(customer=customer, instance_name=name).first()


def _exigir_evolution():
    if not partner_evolution_configured():
        raise ValueError("Evolution de parceiro não configurada.")


def _publicar_numero(inst: WhatsappInstance, extra: dict | None = None) -> dict:
    payload = {
        "instance_name": inst.instance_name,
        "rotulo": inst.rotulo,
        "telefone": inst.telefone,
        "status": inst.status,
        "ativo": inst.is_active,
    }
    if extra:
        payload.update(extra)
    return payload


def _aplicar_estado(inst: WhatsappInstance, state: str, phone: str = "") -> None:
    inst.status = state
    inst.last_seen_at = timezone.now()
    fields = ["status", "last_seen_at", "updated_at"]
    if phone:
        inst.telefone = phone[:32]
        fields.append("telefone")
    inst.save(update_fields=list(dict.fromkeys(fields)))


def listar_numeros(customer: WhatsappCustomer) -> list[dict]:
    _exigir_evolution()
    itens = []
    with evolution_target("parceiro"):
        for inst in customer.instances.filter(is_active=True):
            try:
                info = get_connection_state(inst.instance_name)
                _aplicar_estado(inst, info["state"], info.get("phone") or "")
            except EvolutionAPIError as exc:
                logger.info("Parceiro status %s: %s", inst.instance_name, exc)
            itens.append(_publicar_numero(inst))
    return itens


def conectar_numero(customer: WhatsappCustomer, *, cliente_id: str, rotulo: str = "") -> dict:
    _exigir_evolution()
    name = nome_instancia_parceiro(customer.id, cliente_id)
    inst = WhatsappInstance.objects.filter(customer=customer, instance_name=name).first()
    if inst is None:
        usados = customer.instances.filter(is_active=True).count()
        if usados >= int(customer.quota_numeros or 0):
            raise ValueError(f"Cota de números atingida ({customer.quota_numeros}).")
        inst = WhatsappInstance.objects.create(
            customer=customer,
            instance_name=name,
            rotulo=(rotulo or cliente_id or "")[:80],
            status=WhatsappInstance.STATUS_QR,
            is_active=True,
        )
    elif rotulo.strip():
        inst.rotulo = rotulo.strip()[:80]
        inst.save(update_fields=["rotulo", "updated_at"])

    with evolution_target("parceiro"):
        data = create_evolution_instance_with_qr(name)
        try:
            set_instance_webhook(name)
        except EvolutionAPIError as exc:
            logger.warning("Webhook parceiro %s: %s", name, exc)
        try:
            info = get_connection_state(name)
            _aplicar_estado(inst, info["state"], info.get("phone") or "")
        except EvolutionAPIError:
            _aplicar_estado(inst, WhatsappInstance.STATUS_QR)

    qr = _extract_qr_base64(data) if isinstance(data, dict) else None
    pairing = _extract_pairing_code(data) if isinstance(data, dict) else None
    return _publicar_numero(inst, {"qr_base64": qr, "pairing_code": pairing})


def status_numero(customer: WhatsappCustomer, instance_name: str) -> dict:
    _exigir_evolution()
    inst = instancia_do_parceiro(customer, instance_name)
    if not inst:
        raise ValueError("Número não encontrado neste parceiro.")
    with evolution_target("parceiro"):
        info = get_connection_state(inst.instance_name)
    _aplicar_estado(inst, info["state"], info.get("phone") or "")
    return _publicar_numero(inst)


def desconectar_numero(customer: WhatsappCustomer, instance_name: str) -> dict:
    _exigir_evolution()
    inst = instancia_do_parceiro(customer, instance_name)
    if not inst:
        raise ValueError("Número não encontrado neste parceiro.")
    with evolution_target("parceiro"):
        logout_instance(inst.instance_name)
    _aplicar_estado(inst, WhatsappInstance.STATUS_OFF)
    return _publicar_numero(inst)


def enviar_texto_parceiro(customer: WhatsappCustomer, instance_name: str, number: str, text: str) -> dict:
    _exigir_evolution()
    inst = instancia_do_parceiro(customer, instance_name)
    if not inst or not inst.is_active:
        raise ValueError("Número não encontrado neste parceiro.")
    msg = (text or "").strip()
    if not msg:
        raise ValueError("Informe o texto da mensagem.")
    dest = re.sub(r"\D", "", number or "")
    if len(dest) < 10:
        raise ValueError("Informe o telefone de destino (DDD + número).")
    with evolution_target("parceiro"):
        info = get_connection_state(inst.instance_name)
        _aplicar_estado(inst, info["state"], info.get("phone") or "")
        if info["state"] != "connected":
            raise ValueError("Este número não está conectado. Gere o QR e escaneie no celular.")
        result = send_text(inst.instance_name, dest, msg)
    return {"ok": True, "instance_name": inst.instance_name, "para": dest, "resultado": result}


def atualizar_webhook_parceiro(customer: WhatsappCustomer, webhook_url: str) -> str:
    url = (webhook_url or "").strip()
    if url:
        parsed = urlparse(url)
        if parsed.scheme not in ("https", "http") or not parsed.netloc:
            raise ValueError("webhook_url inválida.")
        if parsed.scheme != "https":
            raise ValueError("webhook_url precisa ser HTTPS.")
        url = url[:500]
    customer.webhook_url = url
    customer.save(update_fields=["webhook_url", "updated_at"])
    return url


def aplicar_conexao_parceiro(instance_name: str, data: dict) -> None:
    name = (instance_name or "").strip()
    inst = WhatsappInstance.objects.filter(instance_name=name).select_related("customer").first()
    if not inst:
        return
    state = _normalize_evolution_state(
        (data or {}).get("state") or (data or {}).get("status"),
    )
    phone = ""
    for key in ("ownerJid", "wuid", "phone", "number"):
        val = (data or {}).get(key)
        if isinstance(val, str) and val.strip():
            phone = re.sub(r"\D", "", val.split("@")[0])[:32]
            break
    _aplicar_estado(inst, state, phone)


def encaminhar_evento_parceiro(instance_name: str, event: dict) -> None:
    name = (instance_name or "").strip()
    inst = WhatsappInstance.objects.filter(instance_name=name).select_related("customer").first()
    if not inst:
        return
    url = (inst.customer.webhook_url or "").strip()
    if not url:
        return
    try:
        requests.post(
            url,
            json={
                "gateway": "lwk",
                "customer_id": inst.customer_id,
                "instance_name": name,
                "event": event,
            },
            timeout=8,
            headers={"Content-Type": "application/json", "X-LWK-Gateway": "whatsapp"},
        )
    except requests.RequestException as exc:
        logger.warning("Webhook PHP parceiro %s: %s", inst.customer_id, exc)
