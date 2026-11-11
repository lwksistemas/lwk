"""Pagamento da NF-e para a despesa da clínica.

À vista vira despesa paga. Duplicata com vencimento fica pendente.
Sem essas duas informações, a importação pergunta depois.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

_A_VISTA = {"01", "02", "03", "04", "17", "18"}
_FORMA = {
    "01": "CASH",
    "02": "CASH",
    "03": "CREDIT_CARD",
    "04": "DEBIT_CARD",
    "17": "PIX",
    "18": "TRANSFER",
    "20": "PIX",
}


def _local(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def _dinheiro(valor: str) -> Decimal:
    try:
        return Decimal(str(valor or "0").replace(",", "."))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _data_texto(valor) -> str:
    """Date do banco ou o texto já gravado no objeto."""
    if hasattr(valor, "isoformat"):
        return valor.isoformat()
    return str(valor or "")[:10]


def _data(valor: str) -> str:
    texto = (valor or "")[:10]
    try:
        date.fromisoformat(texto)
    except ValueError:
        return ""
    return texto


def pagamento_da_nfe(inf_nfe, *, data_emissao: str = "", valor_total: str = "0") -> dict:
    """Lê cobr/dup e pag/detPag. Não grava nada."""
    parcelas = []
    indicadores = []
    formas = []
    for el in inf_nfe.iter():
        nome = _local(el.tag)
        if nome == "dup":
            vencimento = ""
            valor = ""
            numero = ""
            for filho in list(el):
                campo = _local(filho.tag)
                texto = (filho.text or "").strip()
                if campo == "dVenc":
                    vencimento = _data(texto)
                elif campo == "vDup":
                    valor = texto
                elif campo == "nDup":
                    numero = texto[:20]
            if vencimento and _dinheiro(valor or valor_total) > 0:
                parcelas.append({
                    "numero": numero,
                    "vencimento": vencimento,
                    "valor": str(_dinheiro(valor or valor_total).quantize(Decimal("0.01"))),
                })
        elif nome == "detPag":
            for filho in list(el):
                campo = _local(filho.tag)
                texto = (filho.text or "").strip()
                if campo == "indPag":
                    indicadores.append(texto)
                elif campo == "tPag":
                    formas.append(texto)

    forma = _FORMA.get(formas[0], "") if formas else ""
    a_vista = bool(indicadores) and all(item == "0" for item in indicadores) and "90" not in formas
    if not indicadores and formas and all(item in _A_VISTA for item in formas):
        a_vista = True
    situacao = "pendente" if parcelas else "pago" if a_vista else "indefinido"
    return {
        "situacao": situacao,
        "forma_pagamento": forma,
        "valor": str(_dinheiro(valor_total).quantize(Decimal("0.01"))),
        "data_emissao": _data(data_emissao),
        "parcelas": parcelas,
    }


def descricao_da_compra(nomes: list[str] | None, *, parcela: int = 1, total: int = 1) -> str:
    """O que foi comprado. Nota e fornecedor ficam nos próprios campos."""
    vistos: list[str] = []
    for nome in nomes or []:
        texto = (nome or "").strip()
        if texto and texto not in vistos:
            vistos.append(texto)
    base = " · ".join(vistos) if vistos else "Compra de estoque"
    if total > 1:
        marca = f" · {parcela}/{total}"
        base = base[: 200 - len(marca)] + marca
    return base[:200]


def descricao_sem_nota(descricao: str, numero: str, fornecedor: str) -> str:
    """Tira o prefixo NF + fornecedor quando a descrição só repete esses campos."""
    desc = (descricao or "").strip()
    nota = (numero or "").strip()
    forn = (fornecedor or "").strip()
    if not desc or not nota:
        return desc
    prefixo = f"NF {nota} — {forn}".strip(" —")
    if desc == prefixo:
        return ""
    marca = f"{prefixo} · "
    if desc.startswith(marca):
        return desc[len(marca):].strip()
    return desc


def montar_lancamentos(
    pagamento: dict,
    *,
    numero: str,
    fornecedor: str,
    chave: str,
    hoje: date | None = None,
    pago: bool | None = None,
    data_vencimento: str = "",
    nomes: list[str] | None = None,
) -> list[dict]:
    """Parcelas prontas para gravar. Lista vazia quando ainda falta a resposta."""
    situacao = pagamento.get("situacao") or "indefinido"
    if situacao == "indefinido":
        if pago is None:
            return []
        situacao = "pago" if pago else "pendente"
    dia = hoje or date.today()
    emissao = _data(str(pagamento.get("data_emissao") or "")) or dia.isoformat()
    fornecedor_nome = (fornecedor or "Fornecedor")[:200]
    numero_nota = (numero or "")[:20]
    chave_nfe = "".join(c for c in (chave or "") if c.isdigit())[:44]
    forma = (pagamento.get("forma_pagamento") or "")[:20]

    if situacao == "pago":
        vencimento = emissao
        return [{
            "descricao": descricao_da_compra(nomes),
            "valor": _dinheiro(pagamento.get("valor")),
            "status": "PAID",
            "data_vencimento": vencimento,
            "data_pagamento": vencimento,
            "forma_pagamento": forma,
            "numero_nota": numero_nota,
            "fornecedor_nome": fornecedor_nome,
            "chave_nfe": chave_nfe,
            "parcela": 1,
            "observacoes": "Lançada pela importação da NF-e.",
        }]

    parcelas = list(pagamento.get("parcelas") or [])
    if not parcelas:
        vencimento = _data(data_vencimento)
        if not vencimento:
            return []
        parcelas = [{
            "numero": "1",
            "vencimento": vencimento,
            "valor": str(_dinheiro(pagamento.get("valor")).quantize(Decimal("0.01"))),
        }]
    total = len(parcelas)
    lancamentos = []
    for indice, parcela in enumerate(parcelas, start=1):
        valor = _dinheiro(parcela.get("valor"))
        if valor <= 0:
            continue
        descricao = descricao_da_compra(nomes, parcela=indice, total=total)
        lancamentos.append({
            "descricao": descricao[:200],
            "valor": valor.quantize(Decimal("0.01")),
            "status": "PENDING",
            "data_vencimento": parcela["vencimento"],
            "data_pagamento": None,
            "forma_pagamento": "",
            "numero_nota": numero_nota,
            "fornecedor_nome": fornecedor_nome,
            "chave_nfe": chave_nfe,
            "parcela": indice,
            "observacoes": "Lançada pela importação da NF-e.",
        })
    return lancamentos


def gravar_despesas_nfe(loja_id: int | None, lancamentos: list[dict]) -> list:
    """Grava as parcelas. A mesma chave não entra duas vezes."""
    from .models import CategoriaDespesa, Despesa

    if not lancamentos:
        return []
    chave = lancamentos[0].get("chave_nfe") or ""
    if chave and Despesa.objects.filter(chave_nfe=chave).exists():
        return list(Despesa.objects.filter(chave_nfe=chave).order_by("parcela"))
    from django.db import IntegrityError, transaction

    categoria = CategoriaDespesa.objects.filter(nome="Fornecedores").first()
    if categoria is None and loja_id:
        categoria = CategoriaDespesa.objects.create(loja_id=loja_id, nome="Fornecedores")
    criadas = []
    for item in lancamentos:
        if item["valor"] <= 0:
            continue
        try:
            with transaction.atomic():
                criada = Despesa.objects.create(loja_id=loja_id, categoria=categoria, **item)
        except IntegrityError:
            criada = Despesa.objects.filter(
                chave_nfe=item.get("chave_nfe") or "", parcela=item.get("parcela") or 1,
            ).first()
        if criada is not None:
            criadas.append(criada)
    return criadas


def publicar_despesa_nfe(
    loja_id: int | None,
    pagamento: dict,
    *,
    numero: str,
    fornecedor: str,
    chave: str,
    pago: bool | None = None,
    data_vencimento: str = "",
    nomes: list[str] | None = None,
) -> dict:
    resumo = resumo_pagamento(pagamento, numero=numero, fornecedor=fornecedor, chave=chave)
    lancamentos = montar_lancamentos(
        pagamento,
        numero=numero,
        fornecedor=fornecedor,
        chave=chave,
        pago=pago,
        data_vencimento=data_vencimento,
        nomes=nomes,
    )
    if not lancamentos:
        return resumo
    gravadas = gravar_despesas_nfe(loja_id, lancamentos)
    if not gravadas:
        return resumo
    resumo["lancado"] = True
    resumo["precisa_resposta"] = False
    resumo["situacao"] = "pago" if gravadas[0].status == "PAID" else "pendente"
    resumo["parcelas"] = [
        {"vencimento": _data_texto(item.data_vencimento), "valor": str(item.valor), "numero": str(item.parcela)}
        for item in gravadas
    ]
    return resumo


def resumo_pagamento(pagamento: dict, *, numero: str, fornecedor: str, chave: str) -> dict:
    return {
        "lancado": False,
        "precisa_resposta": pagamento.get("situacao") == "indefinido",
        "situacao": pagamento.get("situacao") or "indefinido",
        "valor": pagamento.get("valor") or "0.00",
        "numero": numero or "",
        "fornecedor": fornecedor or "",
        "chave": chave or "",
        "data_emissao": pagamento.get("data_emissao") or "",
        "forma_pagamento": pagamento.get("forma_pagamento") or "",
        "parcelas": pagamento.get("parcelas") or [],
    }
