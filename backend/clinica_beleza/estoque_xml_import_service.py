"""
Service para importação de produtos via XML de NF-e (Nota Fiscal Eletrônica).

Parseia o XML e retorna lista de produtos prontos para criação no estoque.
"""
from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)

# Namespace padrão da NF-e
NFE_NS = '{http://www.portalfiscal.inf.br/nfe}'


def _find_text(element, path: str, ns: str = NFE_NS) -> str:
    """Busca texto em elemento XML com ou sem namespace."""
    # Tentar com namespace
    el = element.find(path.replace('/', f'/{ns}').replace('//', f'//{ns}'))
    if el is None:
        # Tentar sem namespace (NF-e simples)
        el = element.find(path)
    if el is None:
        # Tentar com prefixo direto
        parts = path.split('/')
        ns_path = '/'.join(f'{ns}{p}' for p in parts)
        el = element.find(ns_path)
    return (el.text or '').strip() if el is not None else ''


def _parse_decimal(value: str) -> Decimal:
    """Converte string para Decimal, retorna 0 se inválido."""
    try:
        return Decimal(value.replace(',', '.'))
    except (InvalidOperation, ValueError):
        return Decimal('0')


def _parse_date(value: str) -> Optional[date]:
    """Converte YYYY-MM-DD para date."""
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def parse_nfe_xml(xml_content: bytes) -> dict:
    """
    Parseia XML de NF-e e extrai produtos.

    Args:
        xml_content: Conteúdo do arquivo XML em bytes.

    Returns:
        dict com:
            - 'numero_nota': número da NF
            - 'fornecedor': nome do emitente
            - 'data_emissao': data de emissão
            - 'produtos': lista de dicts com dados de cada produto
            - 'total_produtos': quantidade de itens encontrados
    """
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        raise ValueError(f'XML inválido: {e}')

    # Remover namespace do root tag para facilitar busca
    # Tentar encontrar <infNFe> em qualquer profundidade
    inf_nfe = None
    for tag in [f'{NFE_NS}infNFe', 'infNFe']:
        inf_nfe = root.find(f'.//{tag}')
        if inf_nfe is not None:
            break

    if inf_nfe is None:
        # Pode ser o próprio root ou estar em <NFe> ou <nfeProc>
        for child in root.iter():
            if 'infNFe' in (child.tag.split('}')[-1] if '}' in child.tag else child.tag):
                inf_nfe = child
                break

    if inf_nfe is None:
        raise ValueError('Estrutura de NF-e não encontrada no XML.')

    # Dados da nota
    numero_nota = _find_text(inf_nfe, 'ide/nNF') or _find_text(inf_nfe, f'{NFE_NS}ide/{NFE_NS}nNF')
    data_emissao = _find_text(inf_nfe, 'ide/dhEmi') or _find_text(inf_nfe, f'{NFE_NS}ide/{NFE_NS}dhEmi')
    if data_emissao:
        data_emissao = data_emissao[:10]  # Pegar só YYYY-MM-DD

    # Emitente (fornecedor)
    fornecedor = _find_text(inf_nfe, 'emit/xNome') or _find_text(inf_nfe, f'{NFE_NS}emit/{NFE_NS}xNome')

    # Produtos
    produtos = []
    for det in inf_nfe.iter():
        tag_name = det.tag.split('}')[-1] if '}' in det.tag else det.tag
        if tag_name != 'det':
            continue

        prod = None
        for child in det:
            child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if child_tag == 'prod':
                prod = child
                break

        if prod is None:
            continue

        def get_prod_text(field: str) -> str:
            for el in prod:
                el_tag = el.tag.split('}')[-1] if '}' in el.tag else el.tag
                if el_tag == field:
                    return (el.text or '').strip()
            return ''

        nome = get_prod_text('xProd')
        if not nome:
            continue

        # Lote e validade (pode estar em <rastro> ou <med>)
        lote = ''
        validade_str = ''
        for rastro_tag in ['rastro', 'med']:
            for rastro in det.iter():
                r_tag = rastro.tag.split('}')[-1] if '}' in rastro.tag else rastro.tag
                if r_tag == rastro_tag:
                    for r_child in rastro:
                        rc_tag = r_child.tag.split('}')[-1] if '}' in r_child.tag else r_child.tag
                        if rc_tag == 'nLote' and not lote:
                            lote = (r_child.text or '').strip()
                        if rc_tag == 'dVal' and not validade_str:
                            validade_str = (r_child.text or '').strip()

        produto = {
            'nome': nome.upper()[:200],
            'codigo_produto': get_prod_text('cProd'),
            'ncm': get_prod_text('NCM'),
            'unidade_medida': (get_prod_text('uCom') or 'unidade').lower()[:30],
            'quantidade': str(_parse_decimal(get_prod_text('qCom'))),
            'preco_unitario': str(_parse_decimal(get_prod_text('vUnCom'))),
            'valor_total': str(_parse_decimal(get_prod_text('vProd'))),
            'lote': lote[:50],
            'validade': validade_str[:10] if validade_str else None,
        }
        produtos.append(produto)

    return {
        'numero_nota': numero_nota,
        'fornecedor': fornecedor,
        'data_emissao': data_emissao,
        'produtos': produtos,
        'total_produtos': len(produtos),
    }


def importar_produtos_xml(xml_content: bytes, *, categoria: str = 'outro') -> dict:
    """
    Parseia XML e prepara dados formatados para criação no estoque.

    Returns:
        dict com 'nota' (info da NF) e 'produtos' (lista pronta para serializer).
    """
    parsed = parse_nfe_xml(xml_content)

    produtos_para_criar = []
    for item in parsed['produtos']:
        # Limpar valores decimais para 2 casas (compatível com model)
        preco = str(round(float(item['preco_unitario']), 2))
        quantidade = str(round(float(item['quantidade']), 2))

        produtos_para_criar.append({
            'nome': item['nome'],
            'categoria': categoria,
            'marca': parsed['fornecedor'],
            'unidade_medida': item['unidade_medida'],
            'quantidade_atual': quantidade,
            'quantidade_minima': 0,
            'preco_custo': preco,
            'preco_venda': 0,
            'lote': item['lote'],
            'validade': item['validade'] or None,
            'numero_nota': parsed['numero_nota'],
            'observacoes': f"NCM: {item['ncm']}" if item['ncm'] else '',
        })

    return {
        'nota': {
            'numero': parsed['numero_nota'],
            'fornecedor': parsed['fornecedor'],
            'data_emissao': parsed['data_emissao'],
        },
        'produtos': produtos_para_criar,
        'total_produtos': len(produtos_para_criar),
    }
