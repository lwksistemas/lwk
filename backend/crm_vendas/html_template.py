"""Tira script e atributos perigosos do HTML do template. O texto e a formatação ficam."""
from __future__ import annotations

import re
from html import escape
from html.parser import HTMLParser

_TAGS = frozenset({"p", "div", "span", "br", "strong", "b", "em"})
_LIXO = frozenset({"script", "style", "iframe", "object", "embed", "link", "meta", "svg"})
_ALIGN = frozenset({"left", "center", "right", "justify"})
_FONTE = re.compile(r"^[a-z]{1,20}$")
_TAMANHO = re.compile(r"^\d{1,2}$")
_TEM_TAG = re.compile(
    r"<\s*/?\s*(p|div|span|br|script|iframe|b|strong|em|object|embed)\b",
    re.I,
)


class _Limpador(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.partes: list[str] = []
        self._ignorar = 0

    def handle_starttag(self, tag, attrs):
        nome = (tag or "").lower()
        if nome in _LIXO:
            self._ignorar += 1
            return
        if self._ignorar or nome not in _TAGS:
            return
        if nome == "br":
            self.partes.append("<br>")
            return
        self.partes.append(f"<{nome}{_atributos(attrs)}>")

    def handle_endtag(self, tag):
        nome = (tag or "").lower()
        if nome in _LIXO:
            if self._ignorar:
                self._ignorar -= 1
            return
        if self._ignorar or nome not in _TAGS or nome == "br":
            return
        self.partes.append(f"</{nome}>")

    def handle_data(self, data):
        if self._ignorar or not data:
            return
        self.partes.append(escape(data))

    def handle_entityref(self, name):
        if not self._ignorar:
            self.partes.append(f"&{name};")

    def handle_charref(self, name):
        if not self._ignorar:
            self.partes.append(f"&#{name};")


def _atributos(attrs) -> str:
    saida = []
    for chave, valor in attrs:
        chave = (chave or "").lower()
        valor = (valor or "").strip()
        if chave == "data-align" and valor in _ALIGN:
            saida.append(f' data-align="{valor}"')
        elif chave == "data-font" and _FONTE.fullmatch(valor):
            saida.append(f' data-font="{valor}"')
        elif chave == "data-size" and _TAMANHO.fullmatch(valor):
            saida.append(f' data-size="{valor}"')
        elif chave == "data-bold" and valor in ("0", "1"):
            saida.append(f' data-bold="{valor}"')
    return "".join(saida)


def _texto_visivel(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html or "")


def limpar_html_template(conteudo: str | None) -> str:
    """Devolve o texto original quando não há tag. Com tag, remove só o que executa."""
    bruto = conteudo or ""
    if not _TEM_TAG.search(bruto):
        return bruto
    parser = _Limpador()
    parser.feed(bruto)
    parser.close()
    limpo = "".join(parser.partes)
    if _texto_visivel(bruto).strip() and not _texto_visivel(limpo).strip():
        return _texto_visivel(bruto)
    return limpo
