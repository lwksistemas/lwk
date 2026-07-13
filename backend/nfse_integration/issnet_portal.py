"""Extração de tomador/valor da visualização ISSNet (HTML ou PDF)."""
import contextlib
import logging
import re
from decimal import Decimal, InvalidOperation
from io import BytesIO
from typing import Any

logger = logging.getLogger(__name__)

_ROTULOS_TOMADOR = (
    'Razão Social do Tomador',
    'Razao Social do Tomador',
    'Nome/Razão Social do Tomador',
    'Razão Social',
    'Razao Social',
    'Nome/Razão Social',
    'Nome/Razao Social',
)
_ROTULOS_CPF_CNPJ_TOMADOR = (
    'CPF/CNPJ do Tomador',
    'CNPJ/CPF do Tomador',
    'CPF/CNPJ Tomador',
    'CNPJ Tomador',
    'CPF Tomador',
)
_ROTULOS_VALOR = (
    'Valor dos Serviços',
    'Valor dos Servicos',
    'Valor do Serviço',
    'Valor do Servico',
    'Valor Total dos Serviços',
    'Valor Total',
    'Valor da Nota',
    'Valor Serviços',
)
_ROTULOS_DESCRICAO = ('Discriminação', 'Discriminacao', 'Descrição do Serviço', 'Descricao do Servico')
_ROTULOS_COD_VER = ('Código de Verificação', 'Codigo de Verificacao', 'Cód. Verificação')
_ROTULOS_RPS = ('Número do RPS', 'Numero do RPS', 'Nº RPS', 'RPS')


def _limpar_html(texto: str) -> str:
    s = re.sub(r'(?is)<(script|style)\b[^>]*>.*?</\1>', ' ', texto or '')
    s = re.sub(r'(?is)<br\s*/?>', '\n', s)
    s = re.sub(r'(?is)<[^>]+>', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


def _extrair_bloco_tomador(html: str) -> str:
    if not html:
        return ''
    padroes_bloco = (
        r'(?is)Tomador\s*(?:do\s*Servi[cç]o)?.*?(?=Prestador|Servi[cç]o\s*Prestado|Discrimina|Valores|Valor\s*dos|ISS\b)',
        r'(?is)Dados\s*do\s*Tomador.*?(?=Prestador|Discrimina|Valores)',
    )
    for pat in padroes_bloco:
        m = re.search(pat, html)
        if m:
            return m.group(0)
    return html


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


def _extrair_conteudo_span_id(html: str, span_id: str) -> str:
    """Texto de <span id="...">, inclusive tags internas (<b>, etc.)."""
    if not html or not span_id:
        return ''
    m = re.search(
        rf'(?is)<span[^>]*\bid=["\']{re.escape(span_id)}["\'][^>]*>(.*?)</span>',
        html,
    )
    if not m:
        return ''
    return _limpar_html(m.group(1))


def _aplicar_campos_span_issnet(
    html: str,
    out: dict[str, Any],
    *,
    prestador_cnpj: str = '',
) -> None:
    """Campos da página Nota_Digital_204.aspx (Ribeirão Preto / ISSNet)."""
    nome = _extrair_conteudo_span_id(html, 'lblNomeRazaoTomador')
    if nome and nome.lower() not in ('tomador', 'prestador'):
        out['tomador_nome'] = nome[:200]

    doc = _somente_digitos_doc(_extrair_conteudo_span_id(html, 'lblCpfCnpjTomador'))
    if doc and _doc_diferente_prestador(doc, prestador_cnpj):
        out['tomador_cpf_cnpj'] = doc

    valor = _parse_moeda_br(_extrair_conteudo_span_id(html, 'lblValorTotalNota'))
    if valor:
        out['valor'] = valor

    iss_txt = _parse_moeda_br(_extrair_conteudo_span_id(html, 'lblValorISS'))
    if iss_txt:
        out['valor_iss'] = iss_txt

    cod_ver = _extrair_conteudo_span_id(html, 'lblCodigoVerificacao')
    if cod_ver:
        out['codigo_verificacao'] = cod_ver[:50]

    rps_txt = _extrair_conteudo_span_id(html, 'lblNumRPS')
    rps_digits = re.sub(r'\D', '', rps_txt or '')
    if rps_digits:
        with contextlib.suppress(ValueError):
            out['numero_rps'] = int(rps_digits)

    desc = _extrair_conteudo_span_id(html, 'lblDiscriminacao')
    if desc:
        out['servico_descricao'] = desc[:500]


def _doc_diferente_prestador(doc_digits: str, prestador_cnpj: str) -> bool:
    prest = re.sub(r'\D', '', prestador_cnpj or '')
    return bool(doc_digits and doc_digits != prest)


def extrair_detalhes_portal_issnet_html(
    html: str,
    *,
    prestador_cnpj: str = '',
) -> dict[str, Any]:
    """Tenta ler tomador, valor e RPS da página pública de visualização ISSNet."""
    out: dict[str, Any] = {}
    if not (html or '').strip():
        return out

    _aplicar_campos_span_issnet(html, out, prestador_cnpj=prestador_cnpj)

    bloco_tomador = _extrair_bloco_tomador(html)

    tomador = _valor_por_rotulo_html(bloco_tomador, _ROTULOS_TOMADOR)
    if not tomador:
        tomador = _valor_por_rotulo_html(html, _ROTULOS_TOMADOR)
    if tomador and tomador.lower() not in ('tomador', 'prestador') and not out.get('tomador_nome'):
        out['tomador_nome'] = tomador[:200]

    doc = _valor_por_rotulo_html(bloco_tomador, _ROTULOS_CPF_CNPJ_TOMADOR)
    if not doc:
        doc = _valor_por_rotulo_html(bloco_tomador, ('CPF/CNPJ', 'CNPJ/CPF'))
    doc_digits = _somente_digitos_doc(doc)
    if doc_digits and _doc_diferente_prestador(doc_digits, prestador_cnpj) and not out.get('tomador_cpf_cnpj'):
        out['tomador_cpf_cnpj'] = doc_digits

    valor_txt = _valor_por_rotulo_html(html, _ROTULOS_VALOR)
    valor = _parse_moeda_br(valor_txt)
    if valor and not out.get('valor'):
        out['valor'] = valor

    descricao = _valor_por_rotulo_html(html, _ROTULOS_DESCRICAO)
    if descricao and not out.get('servico_descricao'):
        out['servico_descricao'] = descricao[:500]

    cod_ver = _valor_por_rotulo_html(html, _ROTULOS_COD_VER)
    if cod_ver and not out.get('codigo_verificacao'):
        out['codigo_verificacao'] = cod_ver[:50]

    rps_txt = _valor_por_rotulo_html(html, _ROTULOS_RPS)
    rps_digits = re.sub(r'\D', '', rps_txt or '')
    if rps_digits and not out.get('numero_rps'):
        with contextlib.suppress(ValueError):
            out['numero_rps'] = int(rps_digits)

    return out


def _extrair_texto_pdf(content: bytes) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(content))
        partes = []
        for page in reader.pages:
            partes.append(page.extract_text() or '')
        return '\n'.join(partes)
    except Exception as exc:
        logger.warning('Falha ao ler PDF ISSNet: %s', exc)
        return ''


def buscar_detalhes_portal_issnet(
    url: str,
    *,
    prestador_cnpj: str = '',
    timeout: tuple[int, int] = (6, 25),
) -> dict[str, Any]:
    """GET na URL do portal ISSNet e extrai campos visíveis (HTML ou PDF)."""
    u = (url or '').strip()
    if not u.startswith('http'):
        return {}
    try:
        import requests

        r = requests.get(u, timeout=timeout, headers={'User-Agent': 'LWK-Sistemas/CRM'})
        if r.status_code >= 400:
            logger.warning('Portal ISSNet HTTP %s para %s', r.status_code, u[:120])
            return {}
        ctype = (r.headers.get('Content-Type') or '').lower()
        raw = r.content or b''
        if 'pdf' in ctype or u.lower().endswith('.pdf') or raw[:4] == b'%PDF':
            texto = _extrair_texto_pdf(raw)
            det = extrair_detalhes_portal_issnet_html(texto, prestador_cnpj=prestador_cnpj)
        else:
            det = extrair_detalhes_portal_issnet_html(r.text or '', prestador_cnpj=prestador_cnpj)
        if det:
            logger.info(
                'Portal ISSNet detalhes extraídos: %s',
                {k: det[k] for k in det if k != 'servico_descricao'},
            )
        return det
    except Exception as exc:
        logger.warning('Falha ao ler portal ISSNet: %s', exc)
        return {}
