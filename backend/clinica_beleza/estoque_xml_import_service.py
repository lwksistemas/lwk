"""Service para importação de produtos via XML de NF-e (Nota Fiscal Eletrônica).

Parseia o XML e retorna lista de produtos prontos para criação no estoque.
"""
from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal, InvalidOperation
import defusedxml.ElementTree as ET
from defusedxml.common import DefusedXmlException

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
        raise ValueError(f"XML inválido: {e}") from e

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
    from .estoque_nfe_vinculo import custo_comercial_efetivo, fator_da_unidade, gtin_util

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
            "unidade_estoque": u_trib if fator != 1 else u_com,
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

    return {
        "chave": chave,
        "numero_nota": numero_nota,
        "fornecedor": fornecedor,
        "emitente_documento": emit_cnpj,
        "data_emissao": data_emissao,
        "destinatario_documento": dest_documento,
        "destinatario_nome": dest_nome,
        "valor_total": str(round(valor_nf, 2)),
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

        obs = []
        if item.get("ncm"):
            obs.append(f"NCM: {item['ncm']}")
        if item.get("gtin"):
            obs.append(f"GTIN: {item['gtin']}")
        produtos_para_importar.append({
            "nome": item["nome"],
            "codigo_produto": item.get("codigo_produto") or "",
            "gtin": item.get("gtin") or "",
            "documento_fornecedor": parsed.get("emitente_documento") or "",
            "fornecedor": parsed.get("fornecedor") or "",
            "chave": parsed.get("chave") or "",
            "categoria": cat.slug if cat else slug,
            "categoria_id": cat.id if cat else categoria_id,
            "categoria_inferida": slug,
            "categoria_motivo": motivo,
            "ncm": item.get("ncm") or "",
            "unidade_medida": item["unidade_medida"],
            "unidade_estoque": item.get("unidade_estoque") or item["unidade_medida"],
            "quantidade": quantidade,
            "fator": item.get("fator") or "1",
            "preco_custo": preco,
            "valor_desconto": item.get("valor_desconto") or "0.00",
            "valor_despesas": item.get("valor_despesas") or "0.00",
            "data_emissao": parsed.get("data_emissao") or "",
            "lote": item["lote"],
            "validade": item["validade"] or None,
            "numero_nota": parsed["numero_nota"],
            "observacoes": " · ".join(obs),
            "acao": "novo",
            "confianca": "nenhuma",
            "produto_id": None,
            "produto_nome": "",
            "alerta": "",
            "candidatos": [],
            "exige_lote": False,
            "grupo": "",
            "custo_unitario": "",
        })

    _anexar_reconhecimento(produtos_para_importar)

    return {
        "nota": {
            "chave": parsed.get("chave") or "",
            "numero": parsed["numero_nota"],
            "fornecedor": parsed["fornecedor"],
            "data_emissao": parsed["data_emissao"],
            "destinatario_documento": parsed.get("destinatario_documento", ""),
            "destinatario_nome": parsed.get("destinatario_nome", ""),
            "valor_total": parsed.get("valor_total") or "",
        },
        "produtos": produtos_para_importar,
        "total_produtos": len(produtos_para_importar),
    }


def _anexar_reconhecimento(produtos: list[dict]) -> None:
    from .estoque_nfe_vinculo import classificar_item, custo_unitario_estoque, marcar_repetidos, quantidade_estoque
    from .models import ProdutoEstoque, VinculoProdutoFornecedor

    catalogo = list(ProdutoEstoque.objects.filter(is_active=True).values("id", "nome", "unidade_medida", "exige_lote"))
    vinculos = list(VinculoProdutoFornecedor.objects.values("produto_id", "documento", "codigo", "gtin", "fator"))
    for item in produtos:
        sugestao = classificar_item(
            {
                "nome": item.get("nome") or "",
                "codigo": item.get("codigo_produto") or "",
                "gtin": item.get("gtin") or "",
                "documento": item.get("documento_fornecedor") or "",
                "fator": Decimal(str(item.get("fator") or "1")),
            },
            catalogo,
            vinculos,
        )
        item.update(sugestao)
        fator_item = Decimal(str(item.get("fator") or "1"))
        item["quantidade_estoque"] = str(
            quantidade_estoque(Decimal(str(item.get("quantidade") or "0")), fator_item),
        )
        item["custo_unitario"] = str(
            custo_unitario_estoque(Decimal(str(item.get("preco_custo") or "0")), fator_item),
        )
    marcar_repetidos(produtos)


def _data_item(valor):
    if not valor:
        return None
    if isinstance(valor, date):
        return valor
    texto = str(valor)[:10]
    try:
        return date.fromisoformat(texto)
    except ValueError as exc:
        raise ValueError(f"Validade inválida: {valor}") from exc


def _fator_item(item: dict) -> Decimal:
    try:
        fator = Decimal(str(item.get("fator") or "1"))
    except InvalidOperation as exc:
        raise ValueError(f'Fator inválido em "{item.get("nome", "")}".') from exc
    if fator <= 0:
        raise ValueError(f'O fator de "{item.get("nome", "")}" precisa ser maior que zero.')
    return fator


def _motivo_entrada(item: dict, usuario: str) -> str:
    partes = [f"NF {item.get('numero_nota') or '—'}"]
    if item.get("chave"):
        partes.append(str(item["chave"]))
    if item.get("lote"):
        partes.append(f"lote {str(item['lote'])[:20]}")
    if item.get("validade"):
        partes.append(f"val {str(item['validade'])[:10]}")
    if item.get("fornecedor"):
        partes.append(str(item["fornecedor"])[:40])
    if usuario:
        partes.append(usuario[:40])
    return " · ".join(partes)[:200]


def _depois_da_entrada(item: dict, produto, fator: Decimal, quantidade: Decimal, custo: Decimal, validade, usuario: str) -> None:
    from .estoque_lotes import registrar_compra, registrar_entrada_lote

    _lembrar_fornecedor(item, produto, fator, custo)
    registrar_compra(item, produto, fator, quantidade, custo, validade, usuario)
    registrar_entrada_lote(produto, item, quantidade, validade)


def _lembrar_fornecedor(item: dict, produto, fator: Decimal, custo: Decimal) -> None:
    import re

    from .estoque_nfe_vinculo import gtin_util
    from .models import VinculoProdutoFornecedor

    documento = re.sub(r"\D", "", item.get("documento_fornecedor") or "")[:20]
    codigo = (item.get("codigo_produto") or "").strip()[:60]
    gtin = gtin_util(item.get("gtin") or "")
    if not codigo and gtin:
        codigo = f"ean:{gtin}"[:60]
    if not documento or not codigo:
        return
    VinculoProdutoFornecedor.objects.update_or_create(
        documento=documento,
        codigo=codigo,
        defaults={
            "produto": produto,
            "gtin": gtin[:14],
            "fator": fator,
            "preco": custo,
            "nome_no_fornecedor": (item.get("nome") or "")[:200],
        },
    )


def confirmar_importacao_xml(
    produtos_para_importar: list[dict],
    *,
    loja_id: int | None = None,
    usuario: str = "",
) -> dict:
    """Lança a nota inteira ou não lança nada.

    Item com ação vazia (dúvida) interrompe. Itens iguais marcados como novo
    entram no mesmo produto, cada um com a própria movimentação.
    """
    from django.db import transaction

    from .estoque_categorias import resolver_categoria
    from .estoque_nfe_vinculo import (
        custo_unitario_estoque,
        gtin_util,
        normalizar_nome,
        quantidade_estoque,
        rastreio_obrigatorio_faltando,
    )
    from .models import MovimentacaoEstoque, ProdutoEstoque
    from .serializers import ProdutoEstoqueSerializer

    criados = 0
    atualizados = 0
    ignorados = 0
    novos_da_nota: dict[str, ProdutoEstoque] = {}

    with transaction.atomic():
        for item in produtos_para_importar:
            nome = item.get("nome") or "Item"
            acao = (item.get("acao") or "").strip()
            if acao == "ignorar":
                ignorados += 1
                continue
            if acao not in ("vincular", "novo"):
                raise ValueError(f'Confirme "{nome}" antes de lançar: vincular, cadastrar ou ignorar.')

            fator = _fator_item(item)
            quantidade = quantidade_estoque(Decimal(str(item.get("quantidade") or "0")), fator)
            if quantidade <= 0:
                raise ValueError(f'A quantidade de "{nome}" ficou zerada.')
            custo = custo_unitario_estoque(Decimal(str(item.get("preco_custo") or "0")), fator)
            validade = _data_item(item.get("validade"))
            cat = resolver_categoria(
                loja_id=loja_id,
                categoria_id=item.get("categoria_id"),
                slug=item.get("categoria") or "outro",
            )
            motivo = _motivo_entrada(item, usuario)

            if acao == "vincular":
                try:
                    produto_id = int(item.get("produto_id"))
                except (TypeError, ValueError) as exc:
                    raise ValueError(f'Escolha o produto do estoque para "{nome}".') from exc
                existente = ProdutoEstoque.objects.filter(pk=produto_id, is_active=True).first()
                if existente is None:
                    raise ValueError(f'O produto vinculado a "{nome}" não está mais no estoque.')
                if rastreio_obrigatorio_faltando(existente.exige_lote, acao, item.get("lote") or "", validade):
                    raise ValueError(f'"{nome}" exige lote e validade antes de entrar no estoque.')
                _somar_entrada(existente, quantidade, custo, validade, item.get("lote") or "", item.get("numero_nota") or "", cat)
                MovimentacaoEstoque.objects.create(produto=existente, tipo="entrada", quantidade=quantidade, motivo=motivo)
                _depois_da_entrada(item, existente, fator, quantidade, custo, validade, usuario)
                atualizados += 1
                continue

            chave_novo = gtin_util(item.get("gtin") or "") or normalizar_nome(nome)
            ja_criado = novos_da_nota.get(chave_novo) if chave_novo else None
            if ja_criado is not None:
                _somar_entrada(ja_criado, quantidade, custo, validade, item.get("lote") or "", item.get("numero_nota") or "", cat)
                MovimentacaoEstoque.objects.create(produto=ja_criado, tipo="entrada", quantidade=quantidade, motivo=motivo)
                _depois_da_entrada(item, ja_criado, fator, quantidade, custo, validade, usuario)
                atualizados += 1
                continue

            unidade = item.get("unidade_estoque") or item.get("unidade_medida") or "unidade"
            serializer = ProdutoEstoqueSerializer(
                data={
                    "nome": nome,
                    "categoria": (cat.slug if cat else None) or item.get("categoria") or "outro",
                    "marca": "",
                    "unidade_medida": unidade,
                    "quantidade_atual": str(quantidade),
                    "quantidade_minima": 0,
                    "preco_custo": str(custo),
                    "preco_venda": 0,
                    "lote": item.get("lote") or "",
                    "validade": validade.isoformat() if validade else None,
                    "numero_nota": item.get("numero_nota") or "",
                    "observacoes": item.get("observacoes") or "",
                },
                context={"loja_id": loja_id},
            )
            if not serializer.is_valid():
                raise ValueError(f'Não foi possível cadastrar "{nome}".')
            produto_novo = serializer.save(categoria=cat) if cat else serializer.save()
            MovimentacaoEstoque.objects.create(produto=produto_novo, tipo="entrada", quantidade=quantidade, motivo=motivo)
            _depois_da_entrada(item, produto_novo, fator, quantidade, custo, validade, usuario)
            if chave_novo:
                novos_da_nota[chave_novo] = produto_novo
            criados += 1

    return {"criados": criados, "atualizados": atualizados, "ignorados": ignorados, "erros": []}


def _somar_entrada(produto, quantidade: Decimal, custo: Decimal, validade, lote: str, numero_nota: str, cat) -> None:
    produto.quantidade_atual += quantidade
    produto.preco_custo = custo
    if validade and (not produto.validade or validade < produto.validade):
        produto.validade = validade
    if lote:
        produto.lote = str(lote)[:50]
    if numero_nota:
        produto.numero_nota = str(numero_nota)[:50]
    campos = ["quantidade_atual", "preco_custo", "validade", "lote", "numero_nota", "updated_at"]
    if cat and not produto.categoria_id:
        produto.categoria = cat
        campos.append("categoria")
    produto.save(update_fields=campos)
