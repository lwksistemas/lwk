"""Cadastro de fornecedor e catálogo (CSV/TXT). Não altera estoque."""
from __future__ import annotations

import csv
import io
import re
from decimal import Decimal, InvalidOperation

from core.cpf_utils import (
    existe_documento_duplicado,
    mensagem_documento_duplicado,
    somente_digitos_documento,
)

from .models.fornecedores import Fornecedor, FornecedorProduto


class FornecedorError(Exception):
    """Erro de validação no cadastro/catálogo do fornecedor."""


def _formatar_cnpj(digits: str) -> str:
    d = somente_digitos_documento(digits)
    if len(d) != 14:
        raise FornecedorError("Informe um CNPJ válido com 14 dígitos.")
    return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"


def salvar_fornecedor(loja_id: int, data: dict, fornecedor: Fornecedor | None = None) -> Fornecedor:
    cnpj = _formatar_cnpj(str(data.get("cnpj") or ""))
    if existe_documento_duplicado(
        model=Fornecedor,
        field_name="cnpj",
        value=cnpj,
        loja_id=loja_id,
        exclude_pk=getattr(fornecedor, "pk", None),
    ):
        raise FornecedorError(mensagem_documento_duplicado("cnpj", entidade="fornecedor"))

    razao = (data.get("razao_social") or "").strip()
    if not razao:
        raise FornecedorError("Razão social é obrigatória.")

    campos = {
        "cnpj": cnpj,
        "razao_social": razao[:200],
        "nome_fantasia": (data.get("nome_fantasia") or "").strip()[:200],
        "inscricao_estadual": (data.get("inscricao_estadual") or "").strip()[:30],
        "email": (data.get("email") or "").strip()[:254],
        "telefone": (data.get("telefone") or "").strip()[:20],
        "cep": (data.get("cep") or "").strip()[:10],
        "logradouro": (data.get("logradouro") or "").strip()[:200],
        "numero": (data.get("numero") or "").strip()[:20],
        "complemento": (data.get("complemento") or "").strip()[:100],
        "bairro": (data.get("bairro") or "").strip()[:100],
        "municipio": (data.get("municipio") or "").strip()[:100],
        "uf": (data.get("uf") or "").strip().upper()[:2],
        "is_active": bool(data.get("is_active", True)),
    }
    if fornecedor:
        for k, v in campos.items():
            setattr(fornecedor, k, v)
        fornecedor.save()
        return fornecedor
    return Fornecedor.objects.create(loja_id=loja_id, **campos)


_HEADER_MAP = {
    "codigo": "codigo",
    "código": "codigo",
    "cod": "codigo",
    "sku": "codigo",
    "nome": "nome",
    "produto": "nome",
    "descricao": "nome",
    "descrição": "nome",
    "unidade": "unidade",
    "un": "unidade",
    "preco": "preco",
    "preço": "preco",
    "valor": "preco",
    "preco_ref": "preco",
}


def _detectar_delimiter(texto: str) -> str:
    sample = texto[:2000]
    if sample.count(";") >= sample.count(","):
        return ";"
    return ","


def _parse_preco(raw: str) -> Decimal:
    s = (raw or "").strip().replace("R$", "").replace(" ", "")
    if not s:
        return Decimal("0.00")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return Decimal(s).quantize(Decimal("0.01"))
    except InvalidOperation:
        return Decimal("0.00")


def preview_catalogo_arquivo(conteudo: str) -> list[dict]:
    texto = (conteudo or "").lstrip("\ufeff").strip()
    if not texto:
        raise FornecedorError("Arquivo vazio.")
    delim = _detectar_delimiter(texto)
    reader = csv.reader(io.StringIO(texto), delimiter=delim)
    rows = [r for r in reader if any((c or "").strip() for c in r)]
    if not rows:
        raise FornecedorError("Nenhuma linha válida no arquivo.")

    first = [re.sub(r"\s+", " ", (c or "").strip().lower()) for c in rows[0]]
    mapped = [_HEADER_MAP.get(c) for c in first]
    tem_header = any(mapped)

    itens: list[dict] = []
    data_rows = rows[1:] if tem_header else rows
    for raw in data_rows:
        if tem_header:
            rec = {mapped[i]: (raw[i] if i < len(raw) else "") for i in range(len(mapped)) if mapped[i]}
        else:
            rec = {
                "codigo": raw[0] if len(raw) > 0 else "",
                "nome": raw[1] if len(raw) > 1 else "",
                "unidade": raw[2] if len(raw) > 2 else "un",
                "preco": raw[3] if len(raw) > 3 else "0",
            }
        codigo = str(rec.get("codigo") or "").strip()
        nome = str(rec.get("nome") or "").strip()
        if not codigo or not nome:
            continue
        itens.append({
            "codigo": codigo[:60],
            "nome": nome[:200],
            "unidade": (str(rec.get("unidade") or "un").strip() or "un")[:20],
            "preco_ref": str(_parse_preco(str(rec.get("preco") or ""))),
        })
    if not itens:
        raise FornecedorError("Nenhum produto com código e nome encontrado.")
    return itens


def importar_catalogo(fornecedor: Fornecedor, itens: list[dict]) -> dict:
    criados = atualizados = 0
    for item in itens:
        codigo = (item.get("codigo") or "").strip()
        nome = (item.get("nome") or "").strip()
        if not codigo or not nome:
            continue
        obj, created = FornecedorProduto.objects.update_or_create(
            fornecedor=fornecedor,
            codigo=codigo[:60],
            defaults={
                "loja_id": fornecedor.loja_id,
                "nome": nome[:200],
                "unidade": (item.get("unidade") or "un")[:20],
                "preco_ref": _parse_preco(str(item.get("preco_ref") or item.get("preco") or "0")),
            },
        )
        if created:
            criados += 1
        else:
            atualizados += 1
    return {"criados": criados, "atualizados": atualizados, "total": criados + atualizados}
