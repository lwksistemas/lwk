"""Tipos de consulta, convênios e endereço do consultório."""
from __future__ import annotations

import re
import unicodedata

TIPOS_PADRAO = (
    ("primeira", "Primeira consulta"),
    ("consulta", "Consulta"),
    ("retorno", "Retorno"),
)

CONVENIOS_PADRAO = (("PARTICULAR", "particular"),)


def slug_codigo(nome: str) -> str:
    s = unicodedata.normalize("NFD", nome or "")
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s).strip("_").lower()
    return (s or "tipo")[:40]


def montar_endereco(
    logradouro: str = "",
    numero: str = "",
    complemento: str = "",
    bairro: str = "",
    cidade: str = "",
    uf: str = "",
    cep: str = "",
) -> str:
    partes = [p.strip() for p in (logradouro, numero, complemento, bairro, cidade) if p and p.strip()]
    if uf and uf.strip():
        partes.append(uf.strip().upper())
    if cep and cep.strip():
        partes.append(cep.strip())
    return ", ".join(partes)[:240]


def codigo_unico_tipo(nome: str, exclude_id=None) -> str:
    from .models import TipoConsulta

    base = slug_codigo(nome)
    codigo = base
    n = 2
    qs = TipoConsulta.objects.all()
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)
    while qs.filter(codigo=codigo).exists():
        sufixo = f"_{n}"
        codigo = f"{base[: 40 - len(sufixo)]}{sufixo}"
        n += 1
    return codigo


def garantir_tipos_padrao():
    from .models import TipoConsulta

    if TipoConsulta.objects.filter(is_active=True).exists():
        return
    for ordem, (codigo, nome) in enumerate(TIPOS_PADRAO, start=1):
        existente = TipoConsulta.objects.filter(codigo=codigo).first()
        if existente:
            existente.is_active = True
            existente.nome = nome
            existente.ordem = ordem
            existente.save(update_fields=["is_active", "nome", "ordem"])
            continue
        TipoConsulta.objects.create(codigo=codigo, nome=nome, ordem=ordem)


def garantir_convenios_padrao():
    from .models import ConvenioConsultorio

    if ConvenioConsultorio.objects.filter(is_active=True).exists():
        return
    for ordem, (nome, tipo) in enumerate(CONVENIOS_PADRAO, start=1):
        existente = ConvenioConsultorio.objects.filter(nome=nome).first()
        if existente:
            existente.is_active = True
            existente.tipo = tipo
            existente.ordem = ordem
            existente.save(update_fields=["is_active", "tipo", "ordem"])
            continue
        ConvenioConsultorio.objects.create(nome=nome, tipo=tipo, ordem=ordem)


def montar_numero_prontuario(paciente_id: int) -> str:
    from .config_service import get_or_create_config

    prefixo = (get_or_create_config().prontuario_prefixo or "").strip()
    return f"{prefixo}{paciente_id}"[:30]


def aplicar_tipo_na_consulta(validated_data: dict, initial) -> dict:
    from .models import TipoConsulta

    codigo = (validated_data.get("tipo") or "consulta").strip()[:40] or "consulta"
    validated_data["tipo"] = codigo
    tipo = TipoConsulta.objects.filter(codigo=codigo, is_active=True).first()
    if not tipo:
        return validated_data
    origem = initial if initial is not None else {}
    if "duracao_minutos" not in origem and tipo.duracao_minutos:
        validated_data["duracao_minutos"] = tipo.duracao_minutos
    if "valor" not in origem and tipo.valor is not None:
        validated_data["valor"] = tipo.valor
    return validated_data
