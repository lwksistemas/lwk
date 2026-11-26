"""Leitura de XML de NF-e (produtos, lote/validade, pagamento). Sem models de app."""
from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal, InvalidOperation

import defusedxml.ElementTree as ET
from defusedxml.common import DefusedXmlException

logger = logging.getLogger(__name__)

# Namespace padrão da NF-e
NFE_NS = "{http://www.portalfiscal.inf.br/nfe}"


def _find_text(element, path: str, ns: str = NFE_NS) -> str:
    """Busca texto em elemento XML com ou sem namespace."""
    # Tentar sem namespace
    el = element.find(path)
    if el is not None:
        return (el.text or "").strip()

    # Tentar com namespace em cada segmento
    parts = path.split("/")
    ns_path = "/".join(f"{ns}{p}" for p in parts)
    el = element.find(ns_path)
    if el is not None:
        return (el.text or "").strip()

    # Buscar iterando filhos (fallback para XMLs com namespace irregular)
    segments = path.split("/")
    current = element
    for seg in segments:
        found = None
        for child in current:
            child_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if child_tag == seg:
                found = child
                break
        if found is None:
            return ""
        current = found
    return (current.text or "").strip()


def _parse_decimal(value: str) -> Decimal:
    """Converte string para Decimal, retorna 0 se inválido."""
    try:
        return Decimal(value.replace(",", "."))
    except (InvalidOperation, ValueError):
        return Decimal(0)


def _parse_date(value: str) -> date | None:
    """Converte YYYY-MM-DD para date."""
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def _extrair_inf_nfe(root: ET.Element) -> ET.Element:
    """Localiza o elemento infNFe no XML da NF-e. Levanta ValueError se não encontrado."""
    for tag in [f"{NFE_NS}infNFe", "infNFe"]:
        el = root.find(f".//{tag}")
        if el is not None:
            return el
    for child in root.iter():
        local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if local == "infNFe":
            return child
    raise ValueError("Estrutura de NF-e não encontrada no XML.")


def _get_prod_field(prod_node: ET.Element, field: str) -> str:
    """Retorna texto do elemento filho com tag local igual a field."""
    for el in prod_node:
        local = el.tag.split("}")[-1] if "}" in el.tag else el.tag
        if local == field:
            return (el.text or "").strip()
    return ""


def _extrair_lote_validade(det: ET.Element) -> tuple[str, str]:
    """Extrai lote e validade do elemento <det> (via <rastro> ou <med>)."""
    lote = ""
    validade_str = ""
    for rastro_tag in ["rastro", "med"]:
        for rastro in det.iter():
            r_tag = rastro.tag.split("}")[-1] if "}" in rastro.tag else rastro.tag
            if r_tag != rastro_tag:
                continue
            for r_child in rastro:
                rc_tag = r_child.tag.split("}")[-1] if "}" in r_child.tag else r_child.tag
                if rc_tag == "nLote" and not lote:
                    lote = (r_child.text or "").strip()
                if rc_tag == "dVal" and not validade_str:
                    validade_str = (r_child.text or "").strip()
    return lote, validade_str


def parse_nfe_xml(xml_content: bytes) -> dict:
    """Parseia XML de NF-e e extrai produtos.

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
    except (ET.ParseError, DefusedXmlException) as e:
        from nfse_integration.mensagens_erro import ERR_ESTOQUE_XML

        logger.warning("XML de estoque inválido: %s", e)
        raise ValueError(ERR_ESTOQUE_XML) from e

    inf_nfe = _extrair_inf_nfe(root)

    # Dados da nota
    inf_id = inf_nfe.attrib.get("Id") or ""
    chave = "".join(c for c in inf_id if c.isdigit())
    if len(chave) != 44:
        chave = ""
    numero_nota = _find_text(inf_nfe, "ide/nNF")
    data_emissao = _find_text(inf_nfe, "ide/dhEmi")
    if data_emissao:
        data_emissao = data_emissao[:10]  # Pegar só YYYY-MM-DD

    # Emitente (fornecedor)
    fornecedor = _find_text(inf_nfe, "emit/xNome")
    emit_cnpj = _find_text(inf_nfe, "emit/CNPJ") or _find_text(inf_nfe, "emit/CPF")

    # Destinatário (comprador) — CPF ou CNPJ
    dest_cpf = _find_text(inf_nfe, "dest/CPF")
    dest_cnpj = _find_text(inf_nfe, "dest/CNPJ")
    dest_documento = dest_cnpj or dest_cpf
    dest_nome = _find_text(inf_nfe, "dest/xNome")

    # Valor total da NF (ICMSTot/vNF); fallback = soma dos vProd
    valor_nf = _parse_decimal(_find_text(inf_nfe, "total/ICMSTot/vNF"))

    # Produtos
    from .vinculo import (
        custo_comercial_efetivo,
        embalagem_na_descricao,
        fator_da_unidade,
        gtin_util,
    )

    produtos = []
    for det in inf_nfe.iter():
        tag_name = det.tag.split("}")[-1] if "}" in det.tag else det.tag
        if tag_name != "det":
            continue

        prod = next(
            (c for c in det if (c.tag.split("}")[-1] if "}" in c.tag else c.tag) == "prod"), None,
        )
        if prod is None:
            continue

        nome = _get_prod_field(prod, "xProd")
        if not nome:
            continue

        lote, validade_str = _extrair_lote_validade(det)
        q_com = _parse_decimal(_get_prod_field(prod, "qCom"))
        q_trib = _parse_decimal(_get_prod_field(prod, "qTrib"))
        u_com = (_get_prod_field(prod, "uCom") or "unidade").lower()[:30]
        u_trib = (_get_prod_field(prod, "uTrib") or u_com).lower()[:30]
        gtin = gtin_util(_get_prod_field(prod, "cEAN")) or gtin_util(_get_prod_field(prod, "cEANTrib"))
        fator = fator_da_unidade(q_com, q_trib, u_com, u_trib)
        embalagem = embalagem_na_descricao(nome) if fator == 1 else None
        unidade_estoque = u_trib if fator != 1 else u_com
        if embalagem:
            fator = embalagem["quantidade"]
            unidade_estoque = embalagem["unidade"]
        v_un = _parse_decimal(_get_prod_field(prod, "vUnCom"))
        v_prod = _parse_decimal(_get_prod_field(prod, "vProd"))
        v_desc = _parse_decimal(_get_prod_field(prod, "vDesc"))
        v_frete = _parse_decimal(_get_prod_field(prod, "vFrete"))
        v_seg = _parse_decimal(_get_prod_field(prod, "vSeg"))
        v_outro = _parse_decimal(_get_prod_field(prod, "vOutro"))
        preco_liquido = custo_comercial_efetivo(v_un, q_com, v_prod, v_desc, v_frete, v_seg, v_outro)
        produto = {
            "nome": nome.upper()[:200],
            "codigo_produto": _get_prod_field(prod, "cProd")[:60],
            "gtin": gtin,
            "ncm": _get_prod_field(prod, "NCM"),
            "unidade_medida": u_com,
            "unidade_estoque": unidade_estoque,
            "embalagem_quantidade": str(embalagem["quantidade"]) if embalagem else "",
            "embalagem_unidade": embalagem["unidade"] if embalagem else "",
            "quantidade": str(q_com),
            "quantidade_tributavel": str(q_trib),
            "fator": str(fator),
            "preco_unitario": str(preco_liquido.quantize(Decimal("0.01"))),
            "valor_total": str(v_prod),
            "valor_desconto": str(v_desc.quantize(Decimal("0.01"))),
            "valor_despesas": str((v_frete + v_seg + v_outro).quantize(Decimal("0.01"))),
            "lote": lote[:50],
            "validade": validade_str[:10] if validade_str else None,
        }
        produtos.append(produto)

    if valor_nf <= 0 and produtos:
        valor_nf = sum((_parse_decimal(p.get("valor_total") or "0") for p in produtos), start=_parse_decimal("0"))

    from .pagamento import pagamento_da_nfe

    pagamento = pagamento_da_nfe(
        inf_nfe,
        data_emissao=data_emissao or "",
        valor_total=str(round(valor_nf, 2)),
    )

    return {
        "chave": chave,
        "numero_nota": numero_nota,
        "fornecedor": fornecedor,
        "emitente_documento": emit_cnpj,
        "data_emissao": data_emissao,
        "destinatario_documento": dest_documento,
        "destinatario_nome": dest_nome,
        "valor_total": str(round(valor_nf, 2)),
        "pagamento": pagamento,
        "produtos": produtos,
        "total_produtos": len(produtos),
    }
