"""Cadastro de fornecedor e catálogo (CSV/TXT/PDF). Não altera estoque."""
from __future__ import annotations

import csv
import io
import re
import unicodedata
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


CATALOGO_PDF_MAX_BYTES = 8 * 1024 * 1024

_PRECO_RE = re.compile(r"R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2})")
_NOME_RUIDO_RE = re.compile(
    r"^(área|area|técnica|tecnica|volume|intervalo|apresentação|apresentacao|"
    r"aplicação|aplicacao|local|agulha|formulação|formulacao|certificado|"
    r"1 frasco|1 caixa|2 frascos|5 frascos|5 ampolas|10 ampolas|uso |"
    r"protocolo|diluidor para|promove |diminuição |tratamento da|"
    r"anti-aging|regeneração|rejuvenescimento|semana #|intramuscular|"
    r"endovenos)",
    re.I,
)
_SECOES_CATALOGO = {
    "estética",
    "estetica",
    "faciais",
    "corporais",
    "faciais e corporais",
    "capilar",
    "pele e cabelo",
    "ortomolecular",
    "emagrecimento",
    "saúde",
    "saude",
    "next saúde",
    "next saude",
    "anestésicos",
    "anestesicos",
    "cremes faciais",
    "bioestimuladores",
    "clareadores",
    "emagrecedores faciais",
    "gordura localizada",
    "flacidez tissular",
    "desempenho físico",
    "desempenho fisico",
    "saúde da mente",
    "saude da mente",
    "mulher",
    "pós bariátrica",
    "pos bariatrica",
    "sobre nós",
    "sobre nos",
    "uso tópico",
    "uso topico",
    "uso intramuscular",
    "tabela de ativos next",
    "ativonext pharma",
    "formulação",
    "formulacao",
    "certificado de garantia",
    "auxiliar de tratamento",
    "protocolo adjuvante",
    "sachês",
    "saches",
}


def _norm_nome(nome: str) -> str:
    nfd = unicodedata.normalize("NFD", (nome or "").strip().lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def _codigo_de_nome(nome: str) -> str:
    nfd = unicodedata.normalize("NFD", nome)
    ascii_txt = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    slug = re.sub(r"[^A-Za-z0-9]+", "-", ascii_txt).strip("-").upper()
    return (slug[:40] or "PROD").rstrip("-")


def _forca_nome(line: str) -> int:
    """Nome de produto (alto) vs pedaço de fórmula (baixo)."""
    s = re.sub(r"\s+", " ", (line or "")).strip()
    if not s:
        return 0
    if s[0] in "+0123456789%" or ":" in s:
        return 0
    if re.search(r"\d+\s*%\s*\+", s):
        return 0
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return 0
    upper = sum(1 for c in letters if c.isupper()) / len(letters)
    score = 3
    if upper >= 0.7:
        score += 3
    elif upper >= 0.45:
        score += 1
    if re.match(r"^(KIT|CREME|VITAMINA|CAPILAR|BIOESTIMULADOR)\b", s, re.I):
        score += 1
    if re.search(r"\d+\s*(mg|ml|g|ui|mcg)\b", s, re.I) and len(s) < 28:
        score -= 1
    return score


def _eh_nome_produto(line: str) -> bool:
    s = re.sub(r"\s+", " ", (line or "")).strip(" -–—|")
    if len(s) < 3 or len(s) > 70:
        return False
    if _PRECO_RE.search(s):
        return False
    if _NOME_RUIDO_RE.search(s):
        return False
    low = _norm_nome(s)
    if low in _SECOES_CATALOGO:
        return False
    if s.startswith("--") or s.startswith("+"):
        return False
    if not s[0].isalpha():
        return False
    if ":" in s or "tecnologia" in low or " molecula" in low:
        return False
    if "%" in s and re.search(r"\d+\s*(mg|ml)\b", s, re.I):
        return False
    letters = [c for c in s if c.isalpha()]
    if len(letters) < 3:
        return False
    if sum(1 for c in letters if c.isupper()) / len(letters) < 0.28:
        return False
    if s.count(" ") > 8:
        return False
    return _forca_nome(s) >= 3


def _linhas_catalogo(texto: str) -> list[str]:
    texto = (texto or "").replace("\r\n", "\n").replace("\r", "\n")
    texto = re.sub(r"(?i)(garantia)\s*(R\$)", r"\1\n\2", texto)
    texto = re.sub(r"(R\$\s*\d[\d.]*,\d{2})(?=\S)", r"\1\n", texto)
    linhas: list[str] = []
    for raw in texto.splitlines():
        line = re.sub(r"[\t|]+", " ", raw).strip()
        if line:
            linhas.append(line)
    return linhas


def _nome_antes_do_preco(line: str) -> str | None:
    match = _PRECO_RE.search(line)
    if not match:
        return None
    before = line[: match.start()].strip(" \t-–—|")
    before = re.sub(r"(?i)certificado de garantia", "", before).strip(" \t-–—|")
    if before and _eh_nome_produto(before):
        return re.sub(r"\s+", " ", before)
    return None


def _parse_catalogo_texto_livre(texto: str) -> list[dict]:
    """Extrai nome + preço de catálogo em PDF (ex.: tabela de ativos)."""
    itens: list[dict] = []
    usados: set[str] = set()
    last_name: str | None = None
    linhas = _linhas_catalogo(texto)
    i = 0
    while i < len(linhas):
        line = linhas[i]
        nome_linha = _nome_antes_do_preco(line)
        precos = list(_PRECO_RE.finditer(line))
        if nome_linha and precos:
            _acrescentar_item_catalogo(itens, usados, nome_linha, precos[0].group(1))
            last_name = None
            i += 1
            continue
        if _eh_nome_produto(line) and not precos:
            candidato = re.sub(r"\s+", " ", line).strip(" -–—|")
            if not last_name or _forca_nome(candidato) >= _forca_nome(last_name):
                last_name = candidato
            i += 1
            continue
        if precos:
            nome = last_name
            if not nome or _norm_nome(nome) in usados:
                ahead = linhas[i + 1] if i + 1 < len(linhas) else ""
                if _eh_nome_produto(ahead):
                    nome = re.sub(r"\s+", " ", ahead).strip(" -–—|")
                    i += 1
            if nome and _norm_nome(nome) not in usados:
                _acrescentar_item_catalogo(itens, usados, nome, precos[0].group(1))
                last_name = None
        i += 1
    return itens


def _acrescentar_item_catalogo(itens: list[dict], usados: set[str], nome: str, preco_raw: str) -> None:
    key = _norm_nome(nome)
    if not key or key in usados:
        return
    usados.add(key)
    codigo = _codigo_de_nome(nome)
    existentes = {item["codigo"] for item in itens}
    base = codigo
    n = 2
    while codigo in existentes:
        codigo = f"{base[:36]}-{n}"
        n += 1
    itens.append({
        "codigo": codigo[:60],
        "nome": nome[:200],
        "unidade": "un",
        "preco_ref": str(_parse_preco(preco_raw)),
    })


def _extrair_texto_pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise FornecedorError("Leitura de PDF indisponível neste servidor.") from exc
    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:
        raise FornecedorError("Não foi possível abrir o PDF. Envie um arquivo válido.") from exc
    partes: list[str] = []
    for page in reader.pages:
        try:
            partes.append(page.extract_text() or "")
        except Exception:
            continue
    texto = "\n".join(partes).strip()
    if not texto:
        raise FornecedorError(
            "Este PDF não tem texto selecionável (parece imagem). "
            "Peça ao fornecedor a versão em texto ou um CSV/TXT."
        )
    return texto


def preview_catalogo_pdf(data: bytes) -> list[dict]:
    if not data:
        raise FornecedorError("Arquivo vazio.")
    if len(data) > CATALOGO_PDF_MAX_BYTES:
        raise FornecedorError("PDF no máximo 8 MB.")
    texto = _extrair_texto_pdf(data)
    try:
        return preview_catalogo_arquivo(texto)
    except FornecedorError:
        itens = _parse_catalogo_texto_livre(texto)
        if not itens:
            raise FornecedorError(
                "Não encontramos produtos com nome e preço neste PDF. "
                "Confira se o catálogo tem valores em R$ ou envie um CSV/TXT."
            )
        return itens


def preview_catalogo_entrada(conteudo: str | None = None, arquivo=None) -> list[dict]:
    """Lê CSV/TXT (texto) ou PDF (upload) e devolve prévia do catálogo."""
    if arquivo is not None:
        tamanho = getattr(arquivo, "size", None)
        if tamanho and tamanho > CATALOGO_PDF_MAX_BYTES:
            raise FornecedorError("Arquivo no máximo 8 MB.")
        nome = (getattr(arquivo, "name", "") or "").lower()
        data = arquivo.read()
        if nome.endswith(".pdf") or (data[:5] == b"%PDF-"):
            return preview_catalogo_pdf(data)
        return preview_catalogo_arquivo(data.decode("utf-8-sig", errors="replace"))
    return preview_catalogo_arquivo(conteudo or "")


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
