"""Parse de catálogo de fornecedor (CSV/TXT/PDF). Não grava estoque clínico."""
from __future__ import annotations

import csv
import io
import re
import unicodedata
from decimal import Decimal, InvalidOperation

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


CATALOGO_PDF_MAX_BYTES = 8 * 1024 * 1024

_PRECO_RE = re.compile(r"R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2})")
_PRECO_SO_LINHA_RE = re.compile(r"^(?:R\$\s*)?(\d{1,3}(?:\.\d{3})?,\d{2})$")
_PRECO_FIM_RE = re.compile(r"(\d{1,3}(?:\.\d{3})?,\d{2})\s*$")
_CODIGO_LINHA_RE = re.compile(r"(?i)^c[oó]digo\s*:?\s*(\d{2,5})$")
_NOME_RUIDO_RE = re.compile(
    r"^(área|area|técnica|tecnica|volume|intervalo|apresentação|apresentacao|"
    r"aplicação|aplicacao|local|agulha|formulação|formulacao|certificado|"
    r"1 frasco|1 caixa|2 frascos|5 frascos|5 ampolas|10 ampolas|uso |"
    r"protocolo|diluidor para|promove |diminuição |tratamento da|"
    r"anti-aging|regeneração da|rejuvenescimento da|semana #|intramuscular|"
    r"endovenos|ativos para|qualidade|certificada|testado|lançamento|"
    r"caixa com|preço por sessão|preco por sessao|embalagem econômica|"
    r"embalagem economica|dermatologicamente|rev\.|cód ativos)",
    re.I,
)
_INGREDIENTE_SOLTO = {
    "zinco", "cobre", "luteina", "luteína", "astaxantina", "picnogenol",
    "licopeno", "biotina", "fitase", "colina", "taurina", "de calcio",
    "de cálcio", "pantotenato", "selenometionina", "feno grego",
    "cisteina", "cisteína", "vitamina c", "vitamina a", "vitamina b6",
    "magnesio", "magnésio", "laranja moro", "citrus sinenses",
}
_TITULO_SKIP = {
    "ativos para", "ativos", "ativo", "aplicacao id", "aplicacao sc",
    "aplicacao im", "qualidade", "certificada", "testado",
    "dermatologicamente", "lancamento", "formula", "formulacao",
    "formula exclusiva", "fase 1", "fase 2", "2 fases de", "tratamento",
    "beleza em outro nivel", "uso facial", "uso corporal", "face",
    "pescoco", "busto", "maos", "labios", "indicado tambem", "para os",
    "caixa com", "2 sessoes", "preco por sessao", "embalagem economica",
    "sobre nos", "indicado", "ativo",
}
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
    if low in _INGREDIENTE_SOLTO:
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
    brutas: list[str] = []
    for raw in texto.splitlines():
        line = re.sub(r"[\t|]+", " ", raw).strip()
        if line:
            brutas.append(line)
    linhas: list[str] = []
    i = 0
    while i < len(brutas):
        if brutas[i] == "R$" and i + 1 < len(brutas) and _PRECO_SO_LINHA_RE.match(brutas[i + 1]):
            linhas.append(f"R$ {brutas[i + 1]}")
            i += 2
            continue
        linhas.append(brutas[i])
        i += 1
    return linhas


def _preco_da_linha(line: str) -> str | None:
    m = _PRECO_SO_LINHA_RE.match((line or "").strip())
    if m:
        return m.group(1)
    m = _PRECO_RE.search(line or "")
    return m.group(1) if m else None


def _eh_ingrediente(line: str) -> bool:
    s = re.sub(r"\s+", " ", (line or "")).strip()
    if re.search(r"\d+\s*(mg|ml|mcg|ui|%|amp)\b", s, re.I) and not _CODIGO_LINHA_RE.match(s):
        return True
    if s.startswith("+") or s.startswith("*ATIVOS"):
        return True
    return False


def _juntar_titulo(partes: list[str]) -> str:
    if not partes:
        return ""
    out = partes[0].rstrip()
    for p in partes[1:]:
        if out.endswith("-"):
            out = out + p.lstrip()
        else:
            out = f"{out} {p}"
    return re.sub(r"\s+", " ", out).strip()


def _eh_titulo_protocolo(line: str) -> bool:
    s = re.sub(r"\s+", " ", (line or "")).strip(" -–—|")
    if not s or len(s) > 55:
        return False
    if _preco_da_linha(s) or _CODIGO_LINHA_RE.match(s):
        return False
    if _NOME_RUIDO_RE.search(s) or _eh_ingrediente(s):
        return False
    if re.match(r"^\d+\s+sess", s, re.I):
        return False
    low = _norm_nome(s)
    if low in _SECOES_CATALOGO or low in _TITULO_SKIP or low in _INGREDIENTE_SOLTO:
        return False
    if s.startswith("+") or s.startswith("-"):
        return False
    if _eh_nome_produto(s):
        return True
    words = [w for w in re.split(r"[+\s]+", s) if w and w[0].isalpha()]
    if words and all(w[0].isupper() for w in words) and 3 <= len(s) <= 55:
        return True
    letters = [c for c in s if c.isalpha()]
    if s.endswith("-") and s[0].isalpha() and len(s) <= 20:
        return True
    if len(letters) >= 3 and s[0].isalpha() and sum(1 for c in letters if c.isupper()) / len(letters) >= 0.55:
        return True
    return bool(re.match(r"^(NC|50)\b", s, re.I))


def _coletar_titulo(linhas: list[str], start: int, limite: int, step: int) -> str:
    bloco: list[str] = []
    j = start
    while (step < 0 and j >= limite) or (step > 0 and j < limite):
        if abs(start - j) > 10:
            break
        s = linhas[j]
        if _CODIGO_LINHA_RE.match(s):
            break
        if _preco_da_linha(s):
            if bloco:
                break
            j += step
            continue
        if re.search(r"(?i)c[oó]d\s+ativos", s) or _NOME_RUIDO_RE.search(s):
            j += step
            continue
        if _eh_titulo_protocolo(s):
            bloco.append(s)
            if len(bloco) >= 4:
                break
            j += step
            continue
        if bloco:
            break
        j += step
    if step < 0:
        bloco.reverse()
    return _juntar_titulo(bloco)


def _melhor_nome(*nomes: str) -> str:
    valid = []
    for n in nomes:
        if not n:
            continue
        low = _norm_nome(n)
        if low in _INGREDIENTE_SOLTO or low in _TITULO_SKIP:
            continue
        if re.match(r"^\d{3,}", n) or "(" in n:
            continue
        valid.append(n)
    if not valid:
        return ""
    return max(valid, key=lambda n: (_forca_nome(n), len(n)))


def _preco_proximo_codigo(linhas: list[str], idx: int, prev: int, nxt: int) -> str | None:
    antes_j = antes_p = None
    for j in range(idx - 1, prev - 1, -1):
        p = _preco_da_linha(linhas[j])
        if p:
            antes_j, antes_p = j, p
            break
    depois_j = depois_p = None
    for j in range(idx + 1, nxt):
        if _CODIGO_LINHA_RE.match(linhas[j]):
            break
        p = _preco_da_linha(linhas[j])
        if p:
            depois_j, depois_p = j, p
            break
    if antes_p and depois_p:
        return antes_p if (idx - antes_j) <= (depois_j - idx) else depois_p
    return antes_p or depois_p


def _limpar_nome_tabela(resto: str) -> str:
    s = re.sub(r"\s+", " ", resto or "").strip(" *")
    s = re.sub(r"\b(?:EV|IM|SC|ID)(?:/(?:EV|IM|SC|ID))*\b", " ", s, flags=re.I)
    return re.sub(r"\s+", " ", s).strip(" -.*")


def _parece_linha_tabela(resto: str) -> bool:
    return bool(re.search(r"(?i)(\bAMP\b|\bFR\b|Cx\s*\d|fras\.|amp\.)", resto or ""))


def _linha_tabela_completa(resto: str) -> bool:
    if not resto or not _parece_linha_tabela(resto):
        return False
    return bool(_PRECO_FIM_RE.search(resto))


def _fechar_item_tabela(itens: list[dict], usados: set[str], codigo: str, resto: str) -> None:
    m_fim = _PRECO_FIM_RE.search(resto or "")
    if not m_fim or not _parece_linha_tabela(resto):
        return
    nome = _limpar_nome_tabela(resto[: m_fim.start()])
    if nome:
        _acrescentar_item_catalogo(itens, usados, nome, m_fim.group(1), codigo=codigo)


def _parse_tabela_ativos(linhas: list[str], itens: list[dict], usados: set[str]) -> None:
    """Tabela CÓD / ATIVOS / VALOR (ortomolecular PHD)."""
    na_tabela = False
    pendente_cod: str | None = None
    pendente_txt = ""
    pendente_linhas = 0
    for line in linhas:
        if re.search(r"(?i)c[oó]d\s+ativos", line):
            na_tabela = True
            continue
        if not na_tabela:
            continue
        m = re.match(r"^(\d{3,4})(?:\s+\*?\s*(.*))?$", line)
        if m and not (m.group(2) or "").startswith(","):
            if pendente_cod:
                _fechar_item_tabela(itens, usados, pendente_cod, pendente_txt)
            pendente_cod = m.group(1)
            pendente_txt = (m.group(2) or "").strip()
            pendente_linhas = 1
            if _linha_tabela_completa(pendente_txt):
                _fechar_item_tabela(itens, usados, pendente_cod, pendente_txt)
                pendente_cod = None
                pendente_txt = ""
            continue
        if pendente_cod:
            pendente_txt = f"{pendente_txt} {line}".strip()
            pendente_linhas += 1
            if _linha_tabela_completa(pendente_txt):
                _fechar_item_tabela(itens, usados, pendente_cod, pendente_txt)
                pendente_cod = None
                pendente_txt = ""
            elif pendente_linhas >= 8:
                pendente_cod = None
                pendente_txt = ""
    if pendente_cod:
        _fechar_item_tabela(itens, usados, pendente_cod, pendente_txt)


def _parse_produtos_por_codigo(linhas: list[str], itens: list[dict], usados: set[str]) -> None:
    """Kits de protocolo: CÓDIGO 1719 + preço 375,50 (com ou sem R$)."""
    indices = [i for i, line in enumerate(linhas) if _CODIGO_LINHA_RE.match(line)]
    for n, idx in enumerate(indices):
        codigo = _CODIGO_LINHA_RE.match(linhas[idx]).group(1)
        prev = indices[n - 1] + 1 if n else max(0, idx - 24)
        nxt = indices[n + 1] if n + 1 < len(indices) else min(len(linhas), idx + 10)
        preco = _preco_proximo_codigo(linhas, idx, prev, nxt) or "0,00"
        antes = _coletar_titulo(linhas, idx - 1, prev, -1)
        depois = _coletar_titulo(linhas, idx + 1, min(nxt, idx + 7), 1)
        nome = _melhor_nome(antes, depois)
        if not nome or sum(1 for c in nome if c.isalpha()) < 4:
            continue
        _acrescentar_item_catalogo(itens, usados, nome, preco, codigo=codigo)


def _nome_antes_do_preco(line: str) -> str | None:
    match = _PRECO_RE.search(line)
    if not match:
        return None
    before = line[: match.start()].strip(" \t-–—|")
    before = re.sub(r"(?i)certificado de garantia", "", before).strip(" \t-–—|")
    if before and _eh_nome_produto(before):
        return re.sub(r"\s+", " ", before)
    return None


def _parse_catalogo_rs(linhas: list[str], itens: list[dict], usados: set[str]) -> None:
    """Catálogos visuais com preço em R$ (não usa tabela CÓD/VALOR)."""
    last_name: str | None = None
    i = 0
    while i < len(linhas):
        line = linhas[i]
        if re.match(r"(?i)^c[oó]d\.?\s*:?\s*\d{2,5}$", line):
            last_name = None
            i += 1
            continue
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
            janela = " ".join(linhas[max(0, i - 8): i + 8])
            if re.search(r"(?i)c[oó]d(?:igo|\.?)\s*:?\s*\d{2,5}", janela):
                last_name = None
                i += 1
                continue
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


def _parse_catalogo_texto_livre(texto: str) -> list[dict]:
    """Extrai nome + preço de catálogo em PDF (tabela, CÓDIGO ou R$)."""
    itens: list[dict] = []
    usados: set[str] = set()
    linhas = _linhas_catalogo(texto)
    _parse_tabela_ativos(linhas, itens, usados)
    _parse_produtos_por_codigo(linhas, itens, usados)
    _parse_catalogo_rs(linhas, itens, usados)
    return itens


def _acrescentar_item_catalogo(
    itens: list[dict],
    usados: set[str],
    nome: str,
    preco_raw: str,
    codigo: str | None = None,
) -> None:
    nome = re.sub(r"\s+", " ", (nome or "")).strip(" -–—*")
    key = _norm_nome(nome)
    if not key or key in _INGREDIENTE_SOLTO or key in _SECOES_CATALOGO:
        return
    if _NOME_RUIDO_RE.search(nome):
        return
    existentes = {item["codigo"] for item in itens}
    if codigo:
        codigo = str(codigo).strip()[:60]
        if not codigo or codigo in existentes:
            return
    else:
        if key in usados:
            return
        codigo = _codigo_de_nome(nome)
        base = codigo
        n = 2
        while codigo in existentes:
            codigo = f"{base[:36]}-{n}"
            n += 1
        codigo = codigo[:60]
    usados.add(key)
    itens.append({
        "codigo": codigo,
        "nome": nome[:200],
        "unidade": "un",
        "preco_ref": str(_parse_preco(preco_raw)),
    })


def _texto_pagina_pypdf(page) -> str:
    """Canva/iLovePDF devolve vazio no modo layout; o extract padrão funciona."""
    padrao = ""
    try:
        padrao = page.extract_text() or ""
    except Exception:
        padrao = ""
    if padrao.strip():
        return padrao
    try:
        return page.extract_text(extraction_mode="layout") or ""
    except Exception:
        return ""


def _extrair_texto_pdftotext(data: bytes) -> str:
    import shutil
    import subprocess
    import tempfile

    if not shutil.which("pdftotext"):
        return ""
    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
        tmp.write(data)
        tmp.flush()
        try:
            out = subprocess.check_output(
                ["pdftotext", "-layout", "-enc", "UTF-8", tmp.name, "-"],
                stderr=subprocess.DEVNULL,
                timeout=45,
            )
        except (subprocess.SubprocessError, OSError):
            return ""
    return out.decode("utf-8", errors="replace").strip()


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
        partes.append(_texto_pagina_pypdf(page))
    texto = "\n".join(partes).strip()
    if len(texto) < 40:
        texto = _extrair_texto_pdftotext(data) or texto
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
    if _texto_parece_planilha(texto):
        return preview_catalogo_arquivo(texto)
    itens = _parse_catalogo_texto_livre(texto)
    if not itens:
        raise FornecedorError(
            "Não encontramos produtos com nome e preço neste PDF. "
            "Confira se o catálogo tem código/preço ou valores em R$, ou envie um CSV/TXT."
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
