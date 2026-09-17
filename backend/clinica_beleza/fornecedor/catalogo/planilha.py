"""Parse de catálogo em CSV/TXT (planilha)."""
from __future__ import annotations

import csv
import io
import re

from clinica_beleza.fornecedor.catalogo.comum import _parse_preco
from clinica_beleza.fornecedor.errors import FornecedorError

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


def _texto_parece_planilha(texto: str) -> bool:
    """CSV/TXT de verdade tem cabeçalho codigo + nome. Texto de PDF com vírgulas não."""
    primeira = ""
    for linha in (texto or "").lstrip("\ufeff").splitlines():
        if linha.strip():
            primeira = linha
            break
    if not primeira:
        return False
    delim = ";" if primeira.count(";") >= primeira.count(",") else ","
    if "\t" in primeira and primeira.count("\t") >= max(primeira.count(delim), 1):
        delim = "\t"
    colunas = [re.sub(r"\s+", " ", (c or "").strip().lower()) for c in primeira.split(delim)]
    mapped = {_HEADER_MAP.get(c) for c in colunas}
    return "codigo" in mapped and "nome" in mapped


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
