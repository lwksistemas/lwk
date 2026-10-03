"""Painel SuperAdmin: clientes WhatsApp agrupados (lojas LWK + parceiros)."""
from __future__ import annotations

import hashlib
import logging
import re
import secrets
from collections import defaultdict

from superadmin.models import Loja, WhatsappApiKey, WhatsappCustomer
from whatsapp.evolution_cleanup import loja_id_from_instance_name
from whatsapp.evolution_client import (
    _extract_phone,
    _normalize_evolution_state,
    evolution_configured,
    evolution_target,
    fetch_instances,
    partner_evolution_configured,
)

logger = logging.getLogger(__name__)

API_KEY_PREFIX = "lwk_wh_"
EXT_INSTANCE_RE = re.compile(r"^ext_(\d+)(?:_|$)", re.IGNORECASE)
QUOTA_PARCEIRO_MAX = 500
QUOTA_PARCEIRO_PADRAO = 50


def hash_api_key(raw: str) -> str:
    return hashlib.sha256((raw or "").encode("utf-8")).hexdigest()


def _somente_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor or "")


def _mod11(base: str, pesos: list[int]) -> int:
    total = sum(int(base[i]) * pesos[i] for i in range(len(pesos)))
    resto = total % 11
    return 0 if resto < 2 else 11 - resto


def documento_parceiro_valido(valor: str) -> str:
    """CPF (11) ou CNPJ (14) com dígitos verificadores. Retorna só números."""
    digits = _somente_digitos(valor)
    if len(digits) == 11:
        if digits == digits[0] * 11:
            raise ValueError("CPF inválido.")
        d1 = _mod11(digits[:9], list(range(10, 1, -1)))
        d2 = _mod11(digits[:10], list(range(11, 1, -1)))
        if digits[-2:] != f"{d1}{d2}":
            raise ValueError("CPF inválido. Verifique os números.")
        return digits
    if len(digits) == 14:
        if digits == digits[0] * 14:
            raise ValueError("CNPJ inválido.")
        w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        w2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        if _mod11(digits[:12], w1) != int(digits[12]) or _mod11(digits[:13], w2) != int(digits[13]):
            raise ValueError("CNPJ inválido. Verifique os números.")
        return digits
    raise ValueError("Informe um CPF (11 dígitos) ou CNPJ (14 dígitos).")


def gerar_chave_api(documento: str = "") -> tuple[str, str]:
    digits = _somente_digitos(documento)
    meio = f"{digits}_" if digits else ""
    raw = f"{API_KEY_PREFIX}{meio}{secrets.token_urlsafe(32)}"
    return raw, hash_api_key(raw)


def snapshot_evolution_item(item: dict) -> dict:
    if not isinstance(item, dict):
        return {"instance_name": "", "status": "disconnected", "telefone": ""}
    inst = item.get("instance") if isinstance(item.get("instance"), dict) else item
    name = (inst.get("instanceName") or inst.get("name") or "").strip()
    # Evolution v2.3.x usa "connectionStatus" (open/connecting/close) no fetchInstances;
    # versões antigas usavam "status"/"state". Lê todos para não quebrar na troca de versão.
    state_raw = (
        inst.get("connectionStatus")
        or inst.get("status")
        or inst.get("state")
        or item.get("connectionStatus")
        or item.get("status")
        or item.get("state")
    )
    return {
        "instance_name": name,
        "status": _normalize_evolution_state(state_raw),
        "telefone": _extract_phone(inst) or _extract_phone(item),
        "raw_state": (state_raw or "").strip(),
        "profile_name": (inst.get("profileName") or item.get("profileName") or "").strip(),
    }


def _metricas_mensagens_loja(loja) -> dict:
    """Agrega mensagens WhatsApp enviadas da loja (WhatsAppLog vive no schema da loja).

    Retorna totais e janela de 24h/7d. Best-effort: se o schema estiver indisponível,
    retorna zeros (nunca derruba o painel).
    """
    from datetime import timedelta

    from django.db.models import Count, Max, Q
    from django.utils import timezone

    from core.db_config import ensure_loja_database_config
    from whatsapp.models import WhatsAppLog

    vazio = {"total": 0, "enviadas": 0, "falhas": 0, "ultimas_24h": 0, "ultimos_7d": 0, "ultimo_envio": None}
    db_name = getattr(loja, "database_name", None)
    if not db_name or not ensure_loja_database_config(db_name, conn_max_age=0):
        return vazio
    try:
        agora = timezone.now()
        qs = WhatsAppLog.objects.using(db_name).filter(loja_id=loja.id)
        agg = qs.aggregate(
            total=Count("id"),
            enviadas=Count("id", filter=Q(status="enviado")),
            falhas=Count("id", filter=Q(status="falhou")),
            ultimas_24h=Count("id", filter=Q(created_at__gte=agora - timedelta(hours=24))),
            ultimos_7d=Count("id", filter=Q(created_at__gte=agora - timedelta(days=7))),
            ultimo_envio=Max("created_at"),
        )
        return {
            "total": agg["total"] or 0,
            "enviadas": agg["enviadas"] or 0,
            "falhas": agg["falhas"] or 0,
            "ultimas_24h": agg["ultimas_24h"] or 0,
            "ultimos_7d": agg["ultimos_7d"] or 0,
            "ultimo_envio": agg["ultimo_envio"].isoformat() if agg["ultimo_envio"] else None,
        }
    except Exception as exc:
        logger.warning("Painel WhatsApp: métricas da loja %s indisponíveis: %s", loja.id, exc)
        return vazio


def _conexao_loja(loja) -> dict:
    """Lê status/telefone/conectado_desde do WhatsAppConfig da loja (schema da loja)."""
    from core.db_config import ensure_loja_database_config
    from whatsapp.models import WhatsAppConfig

    vazio = {"conectado_desde": None, "numero_salvo": ""}
    db_name = getattr(loja, "database_name", None)
    if not db_name or not ensure_loja_database_config(db_name, conn_max_age=0):
        return vazio
    try:
        cfg = WhatsAppConfig.objects.using(db_name).filter(loja_id=loja.id).first()
        if not cfg:
            return vazio
        return {
            "conectado_desde": cfg.whatsapp_connected_at.isoformat() if cfg.whatsapp_connected_at else None,
            "numero_salvo": (cfg.whatsapp_connected_phone or "").strip(),
        }
    except Exception as exc:
        logger.warning("Painel WhatsApp: conexão da loja %s indisponível: %s", loja.id, exc)
        return vazio


def _chave_publica(key: WhatsappApiKey) -> dict:
    return {
        "id": key.id,
        "nome": key.nome,
        "prefixo": key.prefixo,
        "revogada": bool(key.revoked_at),
        "ultimo_uso": key.last_used_at.isoformat() if key.last_used_at else None,
        "criada_em": key.created_at.isoformat() if key.created_at else None,
    }


def criar_parceiro(*, nome: str, documento: str, quota_numeros: int = QUOTA_PARCEIRO_PADRAO, webhook_url: str = "") -> WhatsappCustomer:
    nome_limpo = (nome or "").strip()
    if not nome_limpo:
        raise ValueError("Informe o nome do parceiro.")
    doc = documento_parceiro_valido(documento)
    if WhatsappCustomer.objects.filter(tipo=WhatsappCustomer.TIPO_PARCEIRO, documento=doc).exists():
        raise ValueError("Já existe um parceiro com este CPF/CNPJ.")
    try:
        quota = max(1, min(int(quota_numeros or QUOTA_PARCEIRO_PADRAO), QUOTA_PARCEIRO_MAX))
    except (TypeError, ValueError):
        quota = QUOTA_PARCEIRO_PADRAO
    return WhatsappCustomer.objects.create(
        tipo=WhatsappCustomer.TIPO_PARCEIRO,
        nome=nome_limpo,
        documento=doc,
        quota_numeros=quota,
        webhook_url=(webhook_url or "").strip(),
        is_active=True,
    )


def emitir_chave(customer: WhatsappCustomer, nome: str = "padrão") -> tuple[WhatsappApiKey, str]:
    if customer.tipo != WhatsappCustomer.TIPO_PARCEIRO:
        raise ValueError("Chave de API só é emitida para parceiros.")
    if not customer.is_active:
        raise ValueError("Parceiro inativo.")
    raw, digest = gerar_chave_api(customer.documento)
    digits = _somente_digitos(customer.documento)
    prefixo = (f"{API_KEY_PREFIX}{digits}" if digits else raw)[:40]
    key = WhatsappApiKey.objects.create(
        customer=customer,
        nome=(nome or "padrão").strip() or "padrão",
        prefixo=prefixo,
        key_hash=digest,
    )
    return key, raw


def buscar_chave(raw: str) -> WhatsappApiKey | None:
    token = (raw or "").strip()
    if not token.startswith(API_KEY_PREFIX):
        return None
    return (
        WhatsappApiKey.objects.select_related("customer")
        .filter(key_hash=hash_api_key(token), revoked_at__isnull=True, customer__is_active=True)
        .first()
    )


def montar_painel() -> dict:
    evolution = {"configured": evolution_configured(), "ok": False, "error": None, "parceiro_ok": False}
    snapshots: list[dict] = []
    if evolution["configured"]:
        try:
            snapshots = [snapshot_evolution_item(item) for item in fetch_instances()]
            snapshots = [s for s in snapshots if s.get("instance_name")]
            evolution["ok"] = True
        except Exception as exc:
            logger.warning("Painel WhatsApp: falha ao listar Evolution: %s", exc)
            evolution["error"] = str(exc)
    else:
        evolution["error"] = "Evolution API não configurada neste ambiente."

    if partner_evolution_configured():
        try:
            with evolution_target("parceiro"):
                partner_snaps = [snapshot_evolution_item(item) for item in fetch_instances()]
            snapshots.extend([s for s in partner_snaps if s.get("instance_name")])
            evolution["parceiro_ok"] = True
        except Exception as exc:
            logger.warning("Painel WhatsApp: falha Evolution parceiro: %s", exc)
            extra = f"Parceiro: {exc}"
            evolution["error"] = f"{evolution['error']} | {extra}" if evolution["error"] else extra

    lojas = {
        loja.id: loja
        for loja in Loja.objects.select_related("tipo_loja", "plano")
    }
    by_loja: dict[int, list[dict]] = defaultdict(list)
    by_parceiro: dict[int, list[dict]] = defaultdict(list)
    orfas: list[dict] = []

    for snap in snapshots:
        name = snap["instance_name"]
        lid = loja_id_from_instance_name(name)
        ext = EXT_INSTANCE_RE.match(name)
        numero = {
            "instance_name": name,
            "telefone": snap["telefone"],
            "status": snap["status"],
            "rotulo": "",
            "profile_name": snap.get("profile_name", ""),
        }
        if lid is not None and lid in lojas:
            by_loja[lid].append(numero)
        elif ext:
            by_parceiro[int(ext.group(1))].append(numero)
        elif lid is not None:
            orfas.append({**numero, "loja_id": lid})
        else:
            orfas.append(numero)

    clientes: list[dict] = []
    for lid, numeros in sorted(by_loja.items(), key=lambda kv: lojas[kv[0]].nome.lower()):
        loja = lojas[lid]
        conexao = _conexao_loja(loja)
        metricas = _metricas_mensagens_loja(loja)
        # Injeta conectado_desde em cada número conectado desta loja.
        for n in numeros:
            n["conectado_desde"] = conexao["conectado_desde"] if n["status"] == "connected" else None
        clientes.append(
            {
                "id": None,
                "tipo": WhatsappCustomer.TIPO_LWK,
                "loja_id": loja.id,
                "nome": loja.nome,
                "slug": loja.slug,
                "documento": loja.cpf_cnpj or "",
                "ativo": loja.is_active,
                "quota_numeros": 1,
                "app": getattr(loja.tipo_loja, "nome", "") if loja.tipo_loja_id else "",
                "chaves": [],
                "numeros": numeros,
                "mensagens": metricas,
            }
        )

    parceiros = WhatsappCustomer.objects.filter(tipo=WhatsappCustomer.TIPO_PARCEIRO).prefetch_related("api_keys")
    vistos = set()
    for p in parceiros:
        vistos.add(p.id)
        clientes.append(
            {
                "id": p.id,
                "tipo": p.tipo,
                "loja_id": None,
                "nome": p.nome,
                "slug": None,
                "documento": p.documento,
                "ativo": p.is_active,
                "quota_numeros": p.quota_numeros,
                "app": "API parceiro",
                "webhook_url": p.webhook_url,
                "chaves": [_chave_publica(k) for k in p.api_keys.all()],
                "numeros": by_parceiro.get(p.id, []),
            }
        )
    for cid, numeros in by_parceiro.items():
        if cid in vistos:
            continue
        clientes.append(
            {
                "id": cid,
                "tipo": WhatsappCustomer.TIPO_PARCEIRO,
                "loja_id": None,
                "nome": f"Parceiro #{cid} (não cadastrado)",
                "slug": None,
                "documento": "",
                "ativo": False,
                "quota_numeros": 0,
                "app": "API parceiro",
                "chaves": [],
                "numeros": numeros,
            }
        )

    if orfas:
        clientes.append(
            {
                "id": None,
                "tipo": "orfao",
                "loja_id": None,
                "nome": "Instâncias sem cliente",
                "slug": None,
                "documento": "",
                "ativo": False,
                "quota_numeros": 0,
                "app": "",
                "chaves": [],
                "numeros": orfas,
            }
        )

    conectados = qr = off = 0
    msgs_total = msgs_24h = msgs_7d = msgs_falhas = 0
    for c in clientes:
        for n in c["numeros"]:
            if n["status"] == "connected":
                conectados += 1
            elif n["status"] == "qr_pending":
                qr += 1
            else:
                off += 1
        m = c.get("mensagens")
        if m:
            msgs_total += m.get("total", 0)
            msgs_24h += m.get("ultimas_24h", 0)
            msgs_7d += m.get("ultimos_7d", 0)
            msgs_falhas += m.get("falhas", 0)

    return {
        "evolution": evolution,
        "resumo": {
            "clientes": len([c for c in clientes if c["tipo"] != "orfao"]),
            "conectados": conectados,
            "aguardando_qr": qr,
            "desconectados": off,
            "parceiros": WhatsappCustomer.objects.filter(tipo=WhatsappCustomer.TIPO_PARCEIRO).count(),
            "mensagens_total": msgs_total,
            "mensagens_24h": msgs_24h,
            "mensagens_7d": msgs_7d,
            "mensagens_falhas": msgs_falhas,
        },
        "clientes": clientes,
    }
