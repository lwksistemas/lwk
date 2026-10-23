"""Lê PDF de tabela comercial ou catálogo e devolve itens para produtos e serviços."""
from __future__ import annotations

import io
import re
import unicodedata
from decimal import Decimal, InvalidOperation

CATALOGO_PDF_MAX_BYTES = 8 * 1024 * 1024

_PRECO_RE = re.compile(r"R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})")
_TABELA_RE = re.compile(r"TABELA\s*(BLUE|GREEN|BLACK|ESSENCIAL)(?:\s*(\d{4}))?", re.I)
_CAPITAL_RE = re.compile(
    r"CAPITAL\s+SEGURADO\s+R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})",
    re.I,
)
_VIGENCIA_RE = re.compile(r"(\d{2}/\d{2}/\d{4}\s+A\s+\d{2}/\d{2}/\d{4})", re.I)
_ESPECIALIDADE_RE = re.compile(
    r"([A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-ZÁÉÍÓÚÂÊÔÃÕÇ ]{2,70}?)(\d)(?=\s|$)"
)

_ODO_DESCRICAO = {
    "D1": "Odontologia com implante e/ou cirurgia, ortodontia e demais especialidades.",
    "D2": "Procedimentos estéticos.",
    "D3": "Cirurgia bucomaxilo.",
    "D4": "Cirurgia estética orofacial (CEOF).",
}


class CatalogoPdfError(Exception):
    pass


def _sem_acento(texto: str) -> str:
    base = unicodedata.normalize("NFD", texto or "")
    return "".join(c for c in base if unicodedata.category(c) != "Mn")


def _norm(texto: str) -> str:
    return re.sub(r"\s+", " ", _sem_acento(texto or "")).strip().upper()


def _precos(linha: str) -> list[str]:
    return _PRECO_RE.findall(linha or "")


def _decimal(texto: str) -> Decimal:
    limpo = (texto or "").replace(".", "").replace(",", ".")
    try:
        return Decimal(limpo)
    except InvalidOperation as exc:
        raise CatalogoPdfError(f"Preço inválido: {texto}") from exc


def _linhas_da_pagina(page) -> list[str]:
    fragmentos: list[tuple[float, float, str]] = []

    def visitor(text, cm, tm, font_dict, font_size):
        bruto = (text or "").strip()
        if bruto:
            fragmentos.append((float(tm[5]), float(tm[4]), bruto))

    page.extract_text(visitor_text=visitor)
    fragmentos.sort(key=lambda item: (-item[0], item[1]))
    linhas: list[str] = []
    atual_y: float | None = None
    buffer: list[tuple[float, str]] = []
    for y, x, texto in fragmentos:
        if atual_y is None or abs(y - atual_y) > 2.8:
            if buffer:
                linhas.append(_juntar_fragmentos(buffer))
            buffer = [(x, texto)]
            atual_y = y
        else:
            buffer.append((x, texto))
    if buffer:
        linhas.append(_juntar_fragmentos(buffer))
    return [linha for linha in linhas if linha]


def _juntar_fragmentos(buffer: list[tuple[float, str]]) -> str:
    ordenados = sorted(buffer, key=lambda item: item[0])
    partes: list[str] = []
    ultimo_x: float | None = None
    for x, texto in ordenados:
        if ultimo_x is not None and abs(x - ultimo_x) < 0.6 and partes and partes[-1] == texto:
            continue
        partes.append(texto)
        ultimo_x = x
    return re.sub(r"\s+", " ", " ".join(partes)).strip()


def _abrir_pdf(data: bytes):
    if not data:
        raise CatalogoPdfError("Arquivo vazio.")
    if len(data) > CATALOGO_PDF_MAX_BYTES:
        raise CatalogoPdfError("PDF no máximo 8 MB.")
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise CatalogoPdfError("Leitura de PDF indisponível neste servidor.") from exc
    try:
        return PdfReader(io.BytesIO(data))
    except Exception as exc:
        raise CatalogoPdfError("Não foi possível abrir o PDF. Envie um arquivo válido.") from exc


def extrair_linhas_pdf(data: bytes) -> list[str]:
    reader = _abrir_pdf(data)
    linhas: list[str] = []
    for page in reader.pages:
        linhas.extend(_linhas_da_pagina(page))
    if len(" ".join(linhas)) < 40:
        raise CatalogoPdfError(
            "Este PDF não tem texto selecionável. Envie a tabela em PDF de texto, não uma imagem."
        )
    return linhas


def _grupos_da_linha(linha: str) -> list[str] | None:
    s = _norm(linha)
    if "SEM PROCEDIMENTOS" in s and "COM PROCEDIMENTOS" in s:
        return ["SEM", "COM"]
    numeros = re.findall(r"\b(?:[1-6]|D[1-4])\b", s)
    if "GRUPO" in s and len(numeros) >= 2:
        return numeros
    if re.fullmatch(r"(?:D[1-4] ){1,3}D[1-4]", s):
        return numeros
    return None


def _rotulo(linha: str) -> str | None:
    s = _norm(_PRECO_RE.sub(" ", linha))
    s = re.sub(r"\s+", " ", s).strip(" -")
    if s == "MENSALIDADE" or s == "VALOR DA MENSALIDADE":
        return "mensalidade"
    if s == "4 PARCELAS":
        return "parcelas"
    if s in {"A VISTA/ANUAL", "A VISTA / ANUAL"}:
        return "anual"
    if s == "EXTENSAO PJ":
        return "extensao"
    if s == "SOMATORIA":
        return "somatoria"
    return None


def _especialidades_da_linha(linha: str) -> list[tuple[str, str]]:
    s = _norm(linha)
    if any(marca in s for marca in ("TABELA", "CAPITAL", "R$", "GRUPO", "MENSALIDADE", "ESPECIALIDADES")):
        return []
    achados = []
    for nome, grupo in _ESPECIALIDADE_RE.findall(s):
        limpo = re.sub(r"\s+", " ", nome).strip()
        if len(limpo) < 4 or limpo in {"TABELA", "PESSOA", "FISICA"}:
            continue
        achados.append((grupo, limpo))
    return achados


def _capital_codigo(texto: str) -> str:
    inteiro = re.sub(r"\D", "", (texto or "").split(",")[0])
    if not inteiro:
        return "0"
    valor = int(inteiro)
    if valor >= 1000:
        return str(valor // 1000)
    return str(valor)


def _area_codigo(area: str) -> str:
    if area == "ODONTOLOGIA":
        return "ODO"
    if area == "DEMAIS":
        return "DEM"
    return "MED"


def _tabela_codigo(tabela: str, retro: bool, ano: str) -> str:
    base = {"BLUE": "BLU", "GREEN": "GRN", "BLACK": "BLK", "ESSENCIAL": "ESS"}.get(tabela, "TAB")
    if retro and tabela == "BLACK":
        base = "BLKR"
    if ano:
        base = f"{base}{ano[-2:]}"
    return base


_CODIGO_ANTERIOR = re.compile(
    r"^(BLU|GRN|BLKR|BLK|ESS)(\d{2})-(MED|ODO|DEM)-(CC|BOL)-(\d+)-([A-Z0-9]+)-(PF|XPJ|PJP)-(MEN|4P|ANU)$"
)


def encurtar_codigo_anadem(codigo: str) -> str | None:
    """Troca o código longo da tabela (BLU26-MED-CC-300-1-PF-MEN) por um curto (B26MC3-1FM)."""
    achado = _CODIGO_ANTERIOR.fullmatch((codigo or "").strip().upper())
    if not achado:
        return None
    tabela, ano, area, pagamento, capital, grupo, publico, cobranca = achado.groups()
    tab = {"BLU": "B", "GRN": "G", "BLKR": "K", "BLK": "L", "ESS": "E"}[tabela]
    area_c = {"MED": "M", "ODO": "O", "DEM": "D"}[area]
    pag = {"CC": "C", "BOL": "B"}[pagamento]
    cap = int(capital)
    if cap >= 100 and cap % 100 == 0:
        cap //= 100
    pub = {"PF": "F", "XPJ": "X", "PJP": "J"}[publico]
    cob = {"MEN": "M", "4P": "4", "ANU": "A"}[cobranca]
    return f"{tab}{ano}{area_c}{pag}{cap}-{grupo}{pub}{cob}"


def pasta_do_grupo(grupo: str) -> str:
    """Pasta do grupo dentro da tabela: GRUPO 1, GRUPO D1, ou o nome do estético."""
    codigo = (grupo or "").strip().upper()
    if not codigo or codigo == "PL":
        return ""
    if codigo == "SEM":
        return "SEM PROCEDIMENTOS ESTÉTICOS"
    if codigo == "COM":
        return "COM PROCEDIMENTOS ESTÉTICOS"
    if codigo.isdigit() or (codigo.startswith("D") and codigo[1:].isdigit()):
        return f"GRUPO {codigo}"
    return ""


_GRUPO_NO_NOME = re.compile(
    r" — (grupo (?:[1-6]|d[1-4])|sem procedimentos est[eé]ticos|com procedimentos est[eé]ticos) — ",
    re.IGNORECASE,
)
_GRUPO_NO_CODIGO = re.compile(
    r"^[BGKLE]\d{2}[MOD][CB]\d+-(PL|SEM|COM|D[1-4]|[1-6])[FXJ][M4A]$",
    re.IGNORECASE,
)
_PAGAMENTO_NO_NOME = re.compile(
    r" — (boleto banc[aá]rio|cart[aã]o de cr[eé]dito)(?: — |$)",
    re.IGNORECASE,
)
_PAGAMENTO_NO_CODIGO = re.compile(
    r"^[BGKLE]\d{2}[MOD]([CB])\d+-(?:PL|SEM|COM|D[1-4]|[1-6])[FXJ][M4A]$",
    re.IGNORECASE,
)


def pasta_do_produto(nome: str, codigo: str = "") -> str:
    """Descobre a pasta do grupo pelo nome já gravado ou pelo código curto."""
    achado = _GRUPO_NO_NOME.search(nome or "")
    if achado:
        texto = achado.group(1).upper()
        if texto.startswith("GRUPO "):
            return pasta_do_grupo(texto.split(" ", 1)[1])
        if texto.startswith("SEM"):
            return pasta_do_grupo("SEM")
        if texto.startswith("COM"):
            return pasta_do_grupo("COM")
    codigo_achado = _GRUPO_NO_CODIGO.fullmatch((codigo or "").strip().upper())
    if codigo_achado:
        return pasta_do_grupo(codigo_achado.group(1))
    return ""


def pasta_do_pagamento(nome: str = "", codigo: str = "", pagamento: str = "") -> str:
    """Pasta do meio de pagamento dentro do grupo."""
    bruto = (pagamento or "").strip().upper()
    if bruto in {"CC", "C", "CARTAO DE CREDITO", "CARTÃO DE CRÉDITO"}:
        return "CARTÃO DE CRÉDITO"
    if bruto in {"BOL", "B", "BOLETO", "BOLETO BANCARIO", "BOLETO BANCÁRIO"}:
        return "BOLETO BANCÁRIO"
    achado = _PAGAMENTO_NO_NOME.search(nome or "")
    if achado:
        return "BOLETO BANCÁRIO" if achado.group(1).upper().startswith("BOLETO") else "CARTÃO DE CRÉDITO"
    codigo_achado = _PAGAMENTO_NO_CODIGO.fullmatch((codigo or "").strip().upper())
    if codigo_achado:
        return "BOLETO BANCÁRIO" if codigo_achado.group(1) == "B" else "CARTÃO DE CRÉDITO"
    return ""


def pastas_do_item(item: dict) -> list[str]:
    """Subpastas da tabela comercial: área, tabela, grupo e meio de pagamento."""
    explicitas = item.get("pastas") or []
    if explicitas:
        nomes = []
        for nome in explicitas:
            limpo = _norm(str(nome))[:80]
            if limpo and limpo not in nomes:
                nomes.append(limpo)
        return nomes[:4]
    tabela = str(item.get("tabela") or "").strip().upper()
    area = str(item.get("area") or "").strip().upper()
    if not tabela or not area:
        return []
    area_nome = {
        "MEDICINA": "MEDICINA",
        "ODONTOLOGIA": "ODONTOLOGIA",
        "DEMAIS": "DEMAIS CATEGORIAS",
    }.get(area, area)
    pastas = [area_nome, f"TABELA {tabela}"]
    grupo = pasta_do_grupo(str(item.get("grupo") or ""))
    if grupo:
        pastas.append(grupo)
        pagamento = pasta_do_pagamento(pagamento=str(item.get("pagamento") or ""))
        if pagamento:
            pastas.append(pagamento)
    return pastas


def _nome_grupo(grupo: str) -> str:
    if grupo == "PL":
        return ""
    if grupo == "SEM":
        return "Sem procedimentos estéticos"
    if grupo == "COM":
        return "Com procedimentos estéticos"
    if grupo.startswith("D"):
        return f"Grupo {grupo}"
    return f"Grupo {grupo}"


def _eh_capital_isolado(texto: str) -> bool:
    """Valores de capital segurado, como 300.000,00. Preço de plano fica abaixo disso."""
    try:
        return _decimal(texto) >= Decimal("100000")
    except CatalogoPdfError:
        return False


def _descricao_grupo(area: str, grupo: str, especialidades: dict[str, dict[str, list[str]]], texto_odo: bool) -> str:
    nomes = especialidades.get(area, {}).get(grupo) or []
    if nomes:
        return "Especialidades: " + ", ".join(nomes) + "."
    if area == "ODONTOLOGIA" and texto_odo and grupo in _ODO_DESCRICAO:
        return _ODO_DESCRICAO[grupo]
    if grupo == "SEM":
        return "Sem procedimentos estéticos."
    if grupo == "COM":
        return "Com procedimentos estéticos."
    return ""


def parse_linhas_tabela_comercial(linhas: list[str]) -> tuple[list[dict], list[str]]:
    """Converte as linhas da tabela comercial em serviços com código, nome, preço e descrição."""
    tabela = ""
    ano = ""
    retro = False
    area = "MEDICINA"
    vigencia = ""
    pagamento = "Cartão de crédito"
    pagamento_cod = "CC"
    capital = ""
    grupos: list[str] = []
    secao = "pf"
    especialidades: dict[str, dict[str, list[str]]] = {}
    coletando: dict[str, list[str]] = {}
    essencial_preco = ""
    essencial_nota = ""
    itens: list[dict] = []
    avisos: list[str] = []
    texto_odo = any("OROFACIAL" in _norm(linha) or "CEOF" in _norm(linha) for linha in linhas)
    vistos: set[str] = set()

    def guardar_especialidades() -> None:
        nonlocal coletando
        if coletando:
            especialidades[area] = coletando
            coletando = {}

    def emitir(grupo: str, preco: str, cobranca: str, publico: str) -> None:
        if not tabela or not preco:
            return
        area_nome = {
            "MEDICINA": "Medicina",
            "ODONTOLOGIA": "Odontologia",
            "DEMAIS": "Demais categorias profissionais",
        }.get(area, area.title())
        cobranca_nome = {
            "mensalidade": "Mensalidade",
            "parcelas": "4 parcelas",
            "anual": "À vista/anual",
        }[cobranca]
        if publico == "pf":
            publico_nome = "Pessoa física"
            publico_cod = "PF"
        elif publico == "extensao":
            publico_nome = "Extensão pessoa jurídica"
            publico_cod = "XPJ"
        else:
            publico_nome = "Pessoa física + extensão PJ"
            publico_cod = "PJP"
        cobranca_cod = {"mensalidade": "MEN", "parcelas": "4P", "anual": "ANU"}[cobranca]
        recorrencia = {"mensalidade": "mensal", "parcelas": "unico", "anual": "anual"}[cobranca]
        codigo_anterior = "-".join(
            [
                _tabela_codigo(tabela, retro, ano),
                _area_codigo(area),
                pagamento_cod,
                _capital_codigo(capital),
                grupo,
                publico_cod,
                cobranca_cod,
            ]
        )[:50]
        codigo = encurtar_codigo_anadem(codigo_anterior) or codigo_anterior
        if codigo in vistos:
            return
        vistos.add(codigo)
        titulo = f"ANADEM {tabela} {ano}".strip()
        if retro:
            titulo += " com retroatividade"
        miolos = [titulo, area_nome, _nome_grupo(grupo), cobranca_nome, pagamento]
        if capital:
            miolos.append(f"capital {capital}")
        nome = " — ".join(parte for parte in miolos if parte)
        partes = [
            f"{titulo}. {area_nome}. {publico_nome}. {cobranca_nome}.",
            f"Pagamento: {pagamento}.",
        ]
        if capital:
            partes.append(f"Capital segurado {capital}.")
        if vigencia:
            partes.append(f"Vigência {vigencia}.")
        if retro:
            partes.append("Com retroatividade de 5 anos.")
        if cobranca == "parcelas":
            partes.append("Valor de cada uma das 4 parcelas.")
        if publico == "extensao":
            partes.append("Acréscimo da extensão de pessoa jurídica sobre a mensalidade da pessoa física.")
        if publico == "bundle":
            partes.append("Soma da pessoa física com a extensão de pessoa jurídica.")
        extra = _descricao_grupo(area, grupo, especialidades, texto_odo)
        if extra:
            partes.append(extra)
        if tabela == "ESSENCIAL" and essencial_nota:
            partes.append(essencial_nota)
        itens.append(
            {
                "codigo": codigo,
                "codigo_anterior": codigo_anterior if codigo_anterior != codigo else "",
                "nome": nome[:255],
                "descricao": " ".join(partes)[:4000],
                "preco": f"{_decimal(preco):.2f}",
                "recorrencia": recorrencia,
                "tipo": "servico",
                "tabela": tabela,
                "area": area,
                "grupo": grupo,
                "pagamento": pagamento_cod,
            }
        )

    def emitir_linha(linha: str) -> None:
        rotulo = _rotulo(linha)
        if not rotulo or not grupos or not tabela:
            return
        if rotulo == "somatoria":
            return
        if secao == "extensao" and rotulo == "mensalidade":
            return
        valores = _precos(linha)
        if len(valores) != len(grupos):
            avisos.append(
                f"Linha {rotulo} da tabela {tabela} ignorada: {len(valores)} preços para {len(grupos)} grupos."
            )
            return
        if rotulo == "extensao":
            publico = "extensao"
            cobranca = "mensalidade"
        elif secao == "extensao":
            publico = "bundle"
            cobranca = rotulo
        else:
            publico = "pf"
            cobranca = rotulo
        for grupo, preco in zip(grupos, valores, strict=True):
            emitir(grupo, preco, cobranca, publico)

    for bruta in linhas:
        linha = re.sub(r"\s+", " ", bruta).strip()
        if not linha or linha.startswith("-"):
            continue
        norm = _norm(linha)
        tabela_match = _TABELA_RE.search(norm)
        if tabela_match:
            guardar_especialidades()
            tabela = tabela_match.group(1).upper()
            if tabela_match.group(2):
                ano = tabela_match.group(2)
            retro = "COM RETROATIV" in norm
            secao = "pf"
            if tabela == "ESSENCIAL":
                area = "MEDICINA"
                pagamento = "Cartão de crédito"
                pagamento_cod = "CC"
                capital = ""
                grupos = []
        if "COM RETROATIV" in norm and "NAO " not in norm and len(norm) < 90:
            retro = True
        if "RETROATIV" in norm and ("NAO INCLUI" in norm or "NAO CONTEMPL" in norm):
            retro = False
        vigencia_match = _VIGENCIA_RE.search(linha)
        if vigencia_match:
            vigencia = vigencia_match.group(1)
        if norm == "MEDICINA":
            area = "MEDICINA"
        elif norm == "ODONTOLOGIA" or norm.startswith("ODONTOLOGIA "):
            area = "ODONTOLOGIA"
        elif "DEMAIS CATEGORIAS" in norm:
            area = "DEMAIS"
        if "ESPECIALIDADES" in norm and "GRUPO" in norm:
            coletando = {}
        for grupo, nome in _especialidades_da_linha(linha):
            coletando.setdefault(grupo, [])
            if nome not in coletando[grupo]:
                coletando[grupo].append(nome)
        capital_match = _CAPITAL_RE.search(norm)
        if capital_match:
            capital = capital_match.group(1)
        elif tabela == "ESSENCIAL" and "CAPITAL SEGURADO" in norm:
            valores = _precos(linha)
            if valores:
                capital = valores[0]
        if "CARTAO DE CREDITO" in norm:
            guardar_especialidades()
            pagamento = "Cartão de crédito"
            pagamento_cod = "CC"
            secao = "pf"
        elif "BOLETO BANCARIO" in norm:
            guardar_especialidades()
            pagamento = "Boleto bancário"
            pagamento_cod = "BOL"
            secao = "pf"
        if "EXTENSAO PESSOA JURIDICA" in norm:
            guardar_especialidades()
            secao = "extensao"
        novos = _grupos_da_linha(linha)
        if novos:
            grupos = novos
        if tabela == "ESSENCIAL":
            if "RECEM-FORMAD" in norm or "RECEM FORMAD" in norm:
                essencial_nota = (
                    "Produto para médicos recém-formados, com contratação em até 12 meses "
                    "da inscrição no CFM. Cobertura por 24 meses."
                )
            valores = _precos(linha)
            if len(valores) == 1 and _eh_capital_isolado(valores[0]) and "MENSALIDADE" not in norm:
                capital = valores[0]
            elif _rotulo(linha) == "mensalidade" and len(valores) == 1:
                essencial_preco = valores[0]
            if essencial_preco and capital:
                emitir("PL", essencial_preco, "mensalidade", "pf")
                essencial_preco = ""
            continue
        emitir_linha(linha)

    guardar_especialidades()
    return itens, avisos


_LINHA_PIPE = re.compile(
    r"^([A-Za-z0-9][A-Za-z0-9-]{1,48})\s*\|\s*(.+?)\s*\|\s*R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})\s*$"
)


def _secao_de_catalogo(linha: str) -> str:
    if "|" in linha or "R$" in linha or len(linha) > 80:
        return ""
    norm = _norm(linha)
    if not norm or norm.startswith("FONTE") or norm.startswith("HTTP") or "CODIGOS CRIADOS" in norm:
        return ""
    if "PRODUTOS E PREC" in norm:
        return ""
    return norm


def _pastas_da_secao(secao: str) -> list[str]:
    partes = [parte.strip() for parte in secao.split(" - ") if parte.strip()]
    if len(partes) == 2 and partes[1] in {"MENSAL", "ANUAL"}:
        return partes
    return [secao] if secao else []


def _parse_catalogo_pipe(linhas: list[str]) -> list[dict]:
    """Lê linhas no formato código | nome | R$ preço, com o título acima virando subpasta."""
    itens = []
    vistos: set[str] = set()
    secao = ""
    for bruta in linhas:
        linha = re.sub(r"\s+", " ", bruta).strip()
        if not linha:
            continue
        match = _LINHA_PIPE.match(linha)
        if not match:
            titulo = _secao_de_catalogo(linha)
            if titulo:
                secao = titulo
            continue
        codigo = match.group(1).upper()[:50]
        if codigo in vistos:
            continue
        vistos.add(codigo)
        nome = match.group(2).strip()
        nome_norm = _norm(nome)
        if " MENSAL" in f" {nome_norm}" or nome_norm.endswith("MENSAL"):
            recorrencia = "mensal"
        elif " ANUAL" in f" {nome_norm}" or nome_norm.endswith("ANUAL"):
            recorrencia = "anual"
        else:
            recorrencia = "unico"
        itens.append(
            {
                "codigo": codigo,
                "nome": nome[:255],
                "descricao": secao.title() if secao else "",
                "preco": f"{_decimal(match.group(3)):.2f}",
                "recorrencia": recorrencia,
                "tipo": "servico",
                "pastas": _pastas_da_secao(secao),
            }
        )
    return itens


def _linhas_de_texto(data: bytes) -> list[str]:
    reader = _abrir_pdf(data)
    linhas: list[str] = []
    for page in reader.pages:
        linhas.extend((page.extract_text() or "").splitlines())
    return linhas


def _parse_catalogo_simples(linhas: list[str]) -> list[dict]:
    itens = []
    vistos: set[str] = set()
    for bruta in linhas:
        linha = re.sub(r"\s+", " ", bruta).strip()
        if not linha or linha.startswith("-"):
            continue
        valores = _precos(linha)
        if len(valores) != 1:
            continue
        nome = _PRECO_RE.sub(" ", linha)
        nome = re.sub(r"\s+", " ", nome).strip(" -|:")
        norm = _norm(nome)
        if len(nome) < 3 or len(nome) > 140:
            continue
        if any(marca in norm for marca in ("CAPITAL SEGURADO", "TABELA ", "OBSERVAC", "PAGINA")):
            continue
        codigo = re.sub(r"[^A-Z0-9]+", "-", norm).strip("-")[:40] or "ITEM"
        if codigo in vistos:
            continue
        vistos.add(codigo)
        itens.append(
            {
                "codigo": codigo[:50],
                "nome": nome[:255],
                "descricao": "",
                "preco": f"{_decimal(valores[0]):.2f}",
                "recorrencia": "unico",
                "tipo": "servico",
            }
        )
    return itens


def preview_catalogo_pdf(data: bytes) -> dict:
    linhas = extrair_linhas_pdf(data)
    itens, avisos = parse_linhas_tabela_comercial(linhas)
    if not itens:
        texto = _linhas_de_texto(data)
        itens = _parse_catalogo_pipe(texto) or _parse_catalogo_simples(texto) or _parse_catalogo_simples(linhas)
    if not itens:
        raise CatalogoPdfError(
            "Não encontramos produtos com código e preço neste PDF. "
            "A tabela precisa ter grupos e valores em R$, ou uma linha com nome e preço."
        )
    return {"itens": itens, "total": len(itens), "avisos": avisos[:20]}
