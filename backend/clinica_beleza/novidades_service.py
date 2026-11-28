"""Regras de negócio das Novidades da clínica."""
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from django.db.models import Max
from django.utils import timezone

from .models import Novidade, NovidadeConfig


def get_or_create_novidade_config(loja_id: int) -> NovidadeConfig:
    cfg, _ = NovidadeConfig.objects.get_or_create(
        loja_id=loja_id,
        defaults={"ativo": True, "intervalo_carrossel": 5},
    )
    return cfg


def _decimal_or_none(value):
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _date_or_none(value):
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _beneficios_list(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()][:8]
    if isinstance(value, str):
        return [p.strip() for p in value.split("\n") if p.strip()][:8]
    return []


def serialize_novidade(item: Novidade) -> dict:
    return {
        "id": item.id,
        "titulo": item.titulo,
        "descricao": item.descricao,
        "imagem_url": item.imagem_url,
        "selo": item.selo,
        "condicao_especial": item.condicao_especial,
        "preco_de": str(item.preco_de) if item.preco_de is not None else None,
        "preco_por": str(item.preco_por) if item.preco_por is not None else None,
        "botao_texto": item.botao_texto,
        "botao_url": item.botao_url,
        "beneficios": item.beneficios if isinstance(item.beneficios, list) else [],
        "ordem": item.ordem,
        "ativo": item.ativo,
        "data_inicio": item.data_inicio.isoformat() if item.data_inicio else None,
        "data_fim": item.data_fim.isoformat() if item.data_fim else None,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


def serialize_config(cfg: NovidadeConfig) -> dict:
    return {
        "id": cfg.id,
        "ativo": cfg.ativo,
        "intervalo_carrossel": cfg.intervalo_carrossel,
    }


def aplicar_campos_novidade(item: Novidade, data: dict) -> Novidade:
    campos_str = [
        "titulo", "descricao", "imagem_url", "selo", "condicao_especial",
        "botao_texto", "botao_url",
    ]
    for campo in campos_str:
        if campo in data:
            setattr(item, campo, (data.get(campo) or "") if campo != "titulo" else (data.get(campo) or item.titulo))
    if "titulo" in data and not str(data.get("titulo") or "").strip():
        raise ValueError("Informe o título da novidade.")
    if "preco_de" in data:
        item.preco_de = _decimal_or_none(data.get("preco_de"))
    if "preco_por" in data:
        item.preco_por = _decimal_or_none(data.get("preco_por"))
    if "beneficios" in data:
        item.beneficios = _beneficios_list(data.get("beneficios"))
    if "ordem" in data:
        try:
            item.ordem = max(0, int(data.get("ordem") or 0))
        except (TypeError, ValueError):
            pass
    if "ativo" in data:
        item.ativo = bool(data.get("ativo"))
    if "data_inicio" in data:
        item.data_inicio = _date_or_none(data.get("data_inicio"))
    if "data_fim" in data:
        item.data_fim = _date_or_none(data.get("data_fim"))
    return item


def proxima_ordem(loja_id: int) -> int:
    atual = Novidade.objects.filter(loja_id=loja_id).aggregate(m=Max("ordem")).get("m")
    return int(atual or 0) + 1


def novidades_publicas_qs(loja_id: int):
    hoje = timezone.localdate()
    qs = Novidade.objects.filter(loja_id=loja_id, ativo=True)
    qs = qs.filter(models_Q_inicio_fim(hoje))
    return qs.order_by("ordem", "id")


def models_Q_inicio_fim(hoje: date):
    from django.db.models import Q

    return (
        (Q(data_inicio__isnull=True) | Q(data_inicio__lte=hoje))
        & (Q(data_fim__isnull=True) | Q(data_fim__gte=hoje))
    )
