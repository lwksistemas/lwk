"""Extração de tomador/valor da página de visualização ISSNet (fallback)."""
import logging
import re
from decimal import Decimal, InvalidOperation
from typing import Any

logger = logging.getLogger(__name__)

_ROTULOS_TOMADOR = (
    'Razão Social',
    'Razao Social',
    'Nome/Razão Social',
    'Nome/Razao Social',
    'Tomador',
)
_ROTULOS_CPF_CNPJ = ('CPF/CNPJ', 'CNPJ/CPF', 'CPF', 'CNPJ')
_ROTULOS_VALOR = (
    'Valor dos Serviços',
    'Valor dos Servicos',
    'Valor do Serviço',
    'Valor do Servico',
    'Valor Total',
    'Valor da Nota',
)
_ROTULOS_DESCRICAO = ('Discriminação', 'Discriminacao', 'Descrição do Serviço', 'Descricao do Servico')
_ROTULOS_COD_VER = ('Código de Verificação', 'Codigo de Verificacao', 'Cód. Verificação')
_ROTULOS_RPS = ('Número do RPS', 'Numero do RPS', 'RPS')


def _limpar_html(texto: str) -> str:
    s = re.sub(r'(?is)<(script|style)\b[^>]*>.*?</\1>', ' ', texto or '')
    s = re.sub(r'(?is)<br\s*/?>', '\n', s)
    s = re.sub(r'(?is)<[^>]+>', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


def _valor_por_rotulo_html(html: str, rotulos: tuple[str, ...]) -> str:
    if not html:
        return ''
    for rotulo in rotulos:
        padroes = (
            rf'(?is){re.escape(rotulo)}\s*</[^>]+>\s*<[^>]+>\s*([^<]+)',
            rf'(?is){re.escape(rotulo)}[^<]*</[^>]+>\s*<[^>]+>\s*([^<]+)',
            rf'(?is){re.escape(rotulo)}\s*[:\-]?\s*</[^>]+>\s*([^<]+)',
            rf'(?is)id="[^"]*{re.escape(rotulo.replace("/", ""))}[^"]*"[^>]*>([^<]+)<',
        )
        for pat in padroes:
            m = re.search(pat, html)
            if m:
                val = _limpar_html(m.group(1))
                if val and val not in ('&nbsp;', '-', '—'):
                    return val
    texto = _limpar_html(html)
    for rotulo in rotulos:
        m = re.search(rf'(?is){re.escape(rotulo)}\s*[:\-]?\s*([^\n|]{2,120})', texto)
        if m:
            val = m.group(1).strip()
            if val:
                return val
    return ''


def _parse_moeda_br(valor_txt: str) -> str:
    s = (valor_txt or '').strip()
    if not s:
        return ''
    s = re.sub(r'[^\d,.\-]', '', s)
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    try:
        d = Decimal(s)
        if d < 0:
            return ''
        return f'{d:.2f}'
    except (InvalidOperation, ValueError):
        return ''


def _somente_digitos_doc(valor_txt: str) -> str:
    digits = re.sub(r'\D', '', valor_txt or '')
    if len(digits) in (11, 14):
        return digits
    return ''


def extrair_detalhes_portal_issnet_html(html: str) -> dict[str, Any]:
    """Tenta ler tomador, valor e RPS da página pública de visualização ISSNet."""
    out: dict[str, Any] = {}
    if not (html or '').strip():
        return out

    tomador = _valor_por_rotulo_html(html, _ROTULOS_TOMADOR)
    if tomador:
        out['tomador_nome'] = tomador[:200]

    doc = _valor_por_rotulo_html(html, _ROTULOS_CPF_CNPJ)
    doc_digits = _somente_digitos_doc(doc)
    if doc_digits:
        out['tomador_cpf_cnpj'] = doc_digits

    valor_txt = _valor_por_rotulo_html(html, _ROTULOS_VALOR)
    valor = _parse_moeda_br(valor_txt)
    if valor:
        out['valor'] = valor

    descricao = _valor_por_rotulo_html(html, _ROTULOS_DESCRICAO)
    if descricao:
        out['servico_descricao'] = descricao[:500]

    cod_ver = _valor_por_rotulo_html(html, _ROTULOS_COD_VER)
    if cod_ver:
        out['codigo_verificacao'] = cod_ver[:50]

    rps_txt = _valor_por_rotulo_html(html, _ROTULOS_RPS)
    rps_digits = re.sub(r'\D', '', rps_txt or '')
    if rps_digits:
        try:
            out['numero_rps'] = int(rps_digits)
        except ValueError:
            pass

    return out


def buscar_detalhes_portal_issnet(url: str, *, timeout: tuple[int, int] = (6, 20)) -> dict[str, Any]:
    """GET na URL do portal ISSNet e extrai campos visíveis."""
    u = (url or '').strip()
    if not u.startswith('http'):
        return {}
    try:
        import requests

        r = requests.get(u, timeout=timeout, headers={'User-Agent': 'LWK-Sistemas/CRM'})
        if r.status_code >= 400:
            logger.warning('Portal ISSNet HTTP %s para %s', r.status_code, u[:120])
            return {}
        det = extrair_detalhes_portal_issnet_html(r.text or '')
        if det:
            logger.info('Portal ISSNet detalhes extraídos: %s', {k: det[k] for k in det if k != 'servico_descricao'})
        return det
    except Exception as exc:
        logger.warning('Falha ao ler portal ISSNet: %s', exc)
        return {}
