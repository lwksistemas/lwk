"""Service para importação de produtos via XML de NF-e (Nota Fiscal Eletrônica).

Parseia o XML e retorna lista de produtos prontos para criação no estoque.
"""
from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal, InvalidOperation
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)

# Namespace padrão da NF-e
NFE_NS = "{http://www.portalfiscal.inf.br/nfe}"

# Inferência por NCM (prefixo) e palavras-chave na descrição
_NCM_PREFIX_SLUG = {
    "3002": "injetavel",   # vacinas, soros, toxinas
    "3003": "medicamentos",
    "3004": "medicamentos",
    "3005": "descartavel",
    "3006": "descartavel",
    "3304": "cosmético",
    "3305": "cosmético",
    "3307": "cosmético",
    "9018": "equipamento",
    "9021": "equipamento",
    "3822": "outro",
}

_KEYWORD_SLUG = [
    (("botox", "toxina", "dysport", "xeomin", "ácido hialurônico", "acido hialuronico",
      "preenchimento", "sculptra", "radiesse", "ellanse"), "injetavel"),
    (("soro", "vitamina c", "glutamina", "nad+", "iv therapy", "soroterapia",
      "ringer", "fisiológico", "fisiologico"), "soroterapia"),
    (("creme", "loção", "locao", "serum facial", "protetor solar", "cosmético", "cosmetico"), "cosmético"),
    (("sering", "agulha", "luva", "gaze", "algodão", "algodao", "descartável", "descartavel",
      "cateter", "scalp", "máscara", "mascara"), "descartavel"),
    (("laser", "aparelho", "equipamento", "ultrassom"), "equipamento"),
    (("medicamento", "comprimido", "cápsula", "capsula", "antibiótico", "antibiotico"), "medicamentos"),
]


def inferir_categoria_slug(*, nome: str = "", ncm: str = "", fallback: str = "outro") -> tuple[str, str]:
    """Infere slug de categoria a partir de NCM e descrição.
    Returns: (slug, motivo) — motivo descreve a regra usada.
    """
    ncm_digits = "".join(c for c in (ncm or "") if c.isdigit())
    if len(ncm_digits) >= 4:
        prefix = ncm_digits[:4]
        if prefix in _NCM_PREFIX_SLUG:
            return _NCM_PREFIX_SLUG[prefix], f"NCM {prefix}"

    nome_l = (nome or "").lower()
    for keywords, slug in _KEYWORD_SLUG:
        for kw in keywords:
            if kw in nome_l:
                return slug, f'palavra "{kw}"'

    return fallback or "outro", "padrão"


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
    except ET.ParseError as e:
        raise ValueError(f"XML inválido: {e}")

    # Remover namespace do root tag para facilitar busca
    # Tentar encontrar <infNFe> em qualquer profundidade
    inf_nfe = None
    for tag in [f"{NFE_NS}infNFe", "infNFe"]:
        inf_nfe = root.find(f".//{tag}")
        if inf_nfe is not None:
            break

    if inf_nfe is None:
        # Pode ser o próprio root ou estar em <NFe> ou <nfeProc>
        for child in root.iter():
            if "infNFe" in (child.tag.split("}")[-1] if "}" in child.tag else child.tag):
                inf_nfe = child
                break

    if inf_nfe is None:
        raise ValueError("Estrutura de NF-e não encontrada no XML.")

    # Dados da nota
    numero_nota = _find_text(inf_nfe, "ide/nNF")
    data_emissao = _find_text(inf_nfe, "ide/dhEmi")
    if data_emissao:
        data_emissao = data_emissao[:10]  # Pegar só YYYY-MM-DD

    # Emitente (fornecedor)
    fornecedor = _find_text(inf_nfe, "emit/xNome")

    # Destinatário (comprador) — CPF ou CNPJ
    dest_cpf = _find_text(inf_nfe, "dest/CPF")
    dest_cnpj = _find_text(inf_nfe, "dest/CNPJ")
    dest_documento = dest_cnpj or dest_cpf
    dest_nome = _find_text(inf_nfe, "dest/xNome")

    # Produtos
    produtos = []
    for det in inf_nfe.iter():
        tag_name = det.tag.split("}")[-1] if "}" in det.tag else det.tag
        if tag_name != "det":
            continue

        prod = None
        for child in det:
            child_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if child_tag == "prod":
                prod = child
                break

        if prod is None:
            continue

        def get_prod_text(field: str, prod_node=prod) -> str:
            for el in prod_node:
                el_tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
                if el_tag == field:
                    return (el.text or "").strip()
            return ""

        nome = get_prod_text("xProd")
        if not nome:
            continue

        # Lote e validade (pode estar em <rastro> ou <med>)
        lote = ""
        validade_str = ""
        for rastro_tag in ["rastro", "med"]:
            for rastro in det.iter():
                r_tag = rastro.tag.split("}")[-1] if "}" in rastro.tag else rastro.tag
                if r_tag == rastro_tag:
                    for r_child in rastro:
                        rc_tag = r_child.tag.split("}")[-1] if "}" in r_child.tag else r_child.tag
                        if rc_tag == "nLote" and not lote:
                            lote = (r_child.text or "").strip()
                        if rc_tag == "dVal" and not validade_str:
                            validade_str = (r_child.text or "").strip()

        produto = {
            "nome": nome.upper()[:200],
            "codigo_produto": get_prod_text("cProd"),
            "ncm": get_prod_text("NCM"),
            "unidade_medida": (get_prod_text("uCom") or "unidade").lower()[:30],
            "quantidade": str(_parse_decimal(get_prod_text("qCom"))),
            "preco_unitario": str(_parse_decimal(get_prod_text("vUnCom"))),
            "valor_total": str(_parse_decimal(get_prod_text("vProd"))),
            "lote": lote[:50],
            "validade": validade_str[:10] if validade_str else None,
        }
        produtos.append(produto)

    return {
        "numero_nota": numero_nota,
        "fornecedor": fornecedor,
        "data_emissao": data_emissao,
        "destinatario_documento": dest_documento,
        "destinatario_nome": dest_nome,
        "produtos": produtos,
        "total_produtos": len(produtos),
    }


def importar_produtos_xml(
    xml_content: bytes,
    *,
    categoria: str = "outro",
    categoria_id: int | None = None,
    loja_id: int | None = None,
    forcar_categoria: bool = False,
) -> dict:
    """Parseia XML e prepara produtos para o estoque.

    Por padrão infere categoria por NCM/descrição; se forcar_categoria=True
    (ou quando o usuário escolheu categoria explícita diferente de 'outro'
    e passou categoria_id), usa a categoria informada como padrão, ainda
    permitindo override por item no preview.

    Returns:
        dict com 'nota' e 'produtos' (lista pronta para criação/atualização).

    """
    from .estoque_categorias import resolver_categoria

    parsed = parse_nfe_xml(xml_content)
    fallback_slug = categoria or "outro"

    produtos_para_importar = []
    for item in parsed["produtos"]:
        preco = str(round(float(item["preco_unitario"]), 2))
        quantidade = str(round(float(item["quantidade"]), 2))

        if forcar_categoria:
            slug = fallback_slug
            motivo = "seleção manual"
        else:
            slug, motivo = inferir_categoria_slug(
                nome=item["nome"],
                ncm=item.get("ncm") or "",
                fallback=fallback_slug,
            )

        cat = resolver_categoria(
            loja_id=loja_id,
            categoria_id=categoria_id if forcar_categoria else None,
            slug=slug,
        )

        produtos_para_importar.append({
            "nome": item["nome"],
            "categoria": cat.slug if cat else slug,
            "categoria_id": cat.id if cat else categoria_id,
            "categoria_inferida": slug,
            "categoria_motivo": motivo,
            "ncm": item.get("ncm") or "",
            "marca": parsed["fornecedor"],
            "unidade_medida": item["unidade_medida"],
            "quantidade": quantidade,
            "preco_custo": preco,
            "lote": item["lote"],
            "validade": item["validade"] or None,
            "numero_nota": parsed["numero_nota"],
            "observacoes": f"NCM: {item['ncm']}" if item["ncm"] else "",
        })

    return {
        "nota": {
            "numero": parsed["numero_nota"],
            "fornecedor": parsed["fornecedor"],
            "data_emissao": parsed["data_emissao"],
            "destinatario_documento": parsed.get("destinatario_documento", ""),
            "destinatario_nome": parsed.get("destinatario_nome", ""),
        },
        "produtos": produtos_para_importar,
        "total_produtos": len(produtos_para_importar),
    }


def confirmar_importacao_xml(
    produtos_para_importar: list[dict],
    *,
    loja_id: int | None = None,
) -> dict:
    """Cria ou atualiza produtos no estoque a partir da lista parseada.
    Se o produto já existe (mesmo nome), soma quantidade e registra movimentação.

    Returns:
        dict com 'criados', 'atualizados', 'erros'.

    """
    from decimal import Decimal

    from .estoque_categorias import resolver_categoria
    from .models import MovimentacaoEstoque, ProdutoEstoque
    from .serializers import ProdutoEstoqueSerializer

    criados = 0
    atualizados = 0
    erros = []

    for item in produtos_para_importar:
        nome = item["nome"]
        quantidade = Decimal(str(item["quantidade"]))
        numero_nota = item.get("numero_nota", "")

        cat = resolver_categoria(
            loja_id=loja_id,
            categoria_id=item.get("categoria_id"),
            slug=item.get("categoria") or "outro",
        )

        existente = ProdutoEstoque.objects.filter(
            nome__iexact=nome, is_active=True,
        ).first()

        if existente:
            existente.quantidade_atual += quantidade
            if item.get("preco_custo"):
                existente.preco_custo = Decimal(str(item["preco_custo"]))
            if item.get("validade") and (not existente.validade or item["validade"] < str(existente.validade)):
                existente.validade = item["validade"]
            if item.get("lote"):
                existente.lote = item["lote"]
            if numero_nota:
                existente.numero_nota = numero_nota
            if cat and not existente.categoria_id:
                existente.categoria = cat
            existente.save(update_fields=[
                "quantidade_atual", "preco_custo", "validade", "lote", "numero_nota",
                "categoria", "updated_at",
            ])
            MovimentacaoEstoque.objects.create(
                produto=existente,
                tipo="entrada",
                quantidade=quantidade,
                motivo=f'NF {numero_nota} - Lote: {item.get("lote", "")} - Val: {item.get("validade", "")}',
            )
            atualizados += 1
        else:
            # Passa slug (não PK) para evitar "Pk inválido" quando o ID
            # do preview/override não existe no schema da loja.
            serializer_data = {
                "nome": nome,
                "categoria": (cat.slug if cat else None) or item.get("categoria") or "outro",
                "marca": item.get("marca", ""),
                "unidade_medida": item.get("unidade_medida", "unidade"),
                "quantidade_atual": str(quantidade),
                "quantidade_minima": 0,
                "preco_custo": item.get("preco_custo", "0"),
                "preco_venda": 0,
                "lote": item.get("lote", ""),
                "validade": item.get("validade"),
                "numero_nota": numero_nota,
                "observacoes": item.get("observacoes", ""),
            }
            serializer = ProdutoEstoqueSerializer(
                data=serializer_data,
                context={"loja_id": loja_id},
            )
            if serializer.is_valid():
                produto_novo = serializer.save(categoria=cat) if cat else serializer.save()
                MovimentacaoEstoque.objects.create(
                    produto=produto_novo,
                    tipo="entrada",
                    quantidade=quantidade,
                    motivo=f'NF {numero_nota} - Lote: {item.get("lote", "")} - Val: {item.get("validade", "")}',
                )
                criados += 1
            else:
                erros.append({"nome": nome, "erros": serializer.errors})

    return {
        "criados": criados,
        "atualizados": atualizados,
        "erros": erros,
    }
