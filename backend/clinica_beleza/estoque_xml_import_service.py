"""Service para importação de produtos via XML de NF-e (Nota Fiscal Eletrônica).

Parseia o XML e retorna lista de produtos prontos para criação no estoque.
"""
from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal, InvalidOperation

import defusedxml.ElementTree as ET

from core.nfe.xml_parser import (  # noqa: F401
    NFE_NS,
    _extrair_inf_nfe,
    _extrair_lote_validade,
    _find_text,
    _get_prod_field,
    _parse_date,
    _parse_decimal,
    parse_nfe_xml,
)

logger = logging.getLogger(__name__)

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
            "embalagem_quantidade": item.get("embalagem_quantidade") or "",
            "embalagem_unidade": item.get("embalagem_unidade") or "",
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
            "pagamento": parsed.get("pagamento") or {},
        },
        "pagamento": parsed.get("pagamento") or {},
        "produtos": produtos_para_importar,
        "total_produtos": len(produtos_para_importar),
    }


def _anexar_reconhecimento(produtos: list[dict]) -> None:
    from .estoque_nfe_vinculo import classificar_item, custo_unitario_estoque, marcar_repetidos, quantidade_estoque
    from .models import ProdutoEstoque, VinculoProdutoFornecedor

    catalogo = list(ProdutoEstoque.objects.filter(is_active=True).values("id", "nome", "unidade_medida", "exige_lote"))
    vinculos = list(
        VinculoProdutoFornecedor.objects.values("produto_id", "documento", "codigo", "gtin", "fator", "uso_consumo"),
    )
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
        embalagem_qtd = Decimal(str(item.get("embalagem_quantidade") or "0"))
        if fator_item == 1:
            item["unidade_estoque"] = item.get("unidade_medida") or item.get("unidade_estoque")
        elif item.get("embalagem_unidade") and fator_item == embalagem_qtd:
            item["unidade_estoque"] = item["embalagem_unidade"]
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


def _lembrar_fornecedor(item: dict, produto, fator: Decimal, custo: Decimal, *, uso_consumo: bool = False) -> None:
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
            "produto": None if uso_consumo else produto,
            "gtin": gtin[:14],
            "fator": fator,
            "preco": custo,
            "nome_no_fornecedor": (item.get("nome") or "")[:200],
            "uso_consumo": uso_consumo,
        },
    )


def nome_do_cadastro(item: dict) -> str:
    """Nome do estoque, do recibo e da consulta. O nome da nota fica no fornecedor."""
    nota = (item.get("nome") or "").strip()
    comercial = (item.get("nome_comercial") or "").strip()
    return (comercial or nota or "Item")[:200]


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
    from .estoque_categorias import resolver_categoria
    from .estoque_service import tenant_atomic
    from .estoque_nfe_vinculo import (
        custo_unitario_estoque,
        decisao_pendente,
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
    consumos = 0
    novos_da_nota: dict[str, ProdutoEstoque] = {}

    with tenant_atomic():
        for item in produtos_para_importar:
            nome = item.get("nome") or "Item"
            acao = (item.get("acao") or "").strip()
            if acao == "ignorar":
                ignorados += 1
                continue
            if acao == "consumo":
                _lembrar_fornecedor(
                    item,
                    None,
                    Decimal("1"),
                    Decimal(str(item.get("preco_custo") or "0")),
                    uso_consumo=True,
                )
                consumos += 1
                continue
            if decisao_pendente(acao, item.get("produto_id")):
                raise ValueError(f'Confirme "{nome}" antes de lançar: vincular, cadastrar, uso e consumo ou ignorar.')

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
                _somar_entrada(existente, quantidade, custo, validade, item.get("lote") or "", item.get("numero_nota") or "", cat, item.get("ncm") or "")
                MovimentacaoEstoque.objects.create(produto=existente, tipo="entrada", quantidade=quantidade, motivo=motivo)
                _depois_da_entrada(item, existente, fator, quantidade, custo, validade, usuario)
                atualizados += 1
                continue

            chave_novo = gtin_util(item.get("gtin") or "") or normalizar_nome(nome)
            ja_criado = novos_da_nota.get(chave_novo) if chave_novo else None
            if ja_criado is not None:
                _somar_entrada(ja_criado, quantidade, custo, validade, item.get("lote") or "", item.get("numero_nota") or "", cat, item.get("ncm") or "")
                MovimentacaoEstoque.objects.create(produto=ja_criado, tipo="entrada", quantidade=quantidade, motivo=motivo)
                _depois_da_entrada(item, ja_criado, fator, quantidade, custo, validade, usuario)
                atualizados += 1
                continue

            unidade = item.get("unidade_estoque") or item.get("unidade_medida") or "unidade"
            nome_estoque = nome_do_cadastro(item)
            ncm = "".join(ch for ch in str(item.get("ncm") or "") if ch.isdigit())[:8]
            dados_produto = {
                "nome": nome_estoque,
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
            }
            if len(ncm) == 8:
                dados_produto["ncm"] = ncm
            serializer = ProdutoEstoqueSerializer(
                data=dados_produto,
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

    return {"criados": criados, "atualizados": atualizados, "ignorados": ignorados, "consumos": consumos, "erros": []}


def _somar_entrada(produto, quantidade: Decimal, custo: Decimal, validade, lote: str, numero_nota: str, cat, ncm: str = "") -> None:
    produto.quantidade_atual += quantidade
    produto.preco_custo = custo
    if validade and (not produto.validade or validade < produto.validade):
        produto.validade = validade
    if lote:
        produto.lote = str(lote)[:50]
    if numero_nota:
        produto.numero_nota = str(numero_nota)[:50]
    campos = ["quantidade_atual", "preco_custo", "validade", "lote", "numero_nota", "updated_at"]
    ncm_digits = "".join(ch for ch in str(ncm or "") if ch.isdigit())[:8]
    if len(ncm_digits) == 8 and not (produto.ncm or "").strip():
        produto.ncm = ncm_digits
        campos.append("ncm")
    if cat and not produto.categoria_id:
        produto.categoria = cat
        campos.append("categoria")
    produto.save(update_fields=campos)
