"""Comissão da prestadora e a parte do vendedor."""
from decimal import Decimal, InvalidOperation

from rest_framework.exceptions import ValidationError

TIPOS_COM_COMISSAO = ("prestadora", "ambos")


def validar_itens_comissao(itens) -> list[dict]:
    if itens is None:
        return []
    if not isinstance(itens, list):
        raise ValueError("Informe os serviços da prestadora.")

    saida = []
    vistos = set()
    for item in itens:
        if not isinstance(item, dict):
            raise ValueError("Item de comissão inválido.")
        try:
            produto_id = int(item.get("produto_servico_id"))
        except (TypeError, ValueError):
            raise ValueError("Escolha um produto ou serviço.") from None
        bruto = item.get("valor")
        if bruto is None or str(bruto).strip() == "":
            continue
        try:
            valor = Decimal(str(bruto).replace(",", ".")).quantize(Decimal("0.01"))
        except (InvalidOperation, TypeError):
            raise ValueError("Informe o valor pago pela prestadora.") from None
        tipo = item.get("tipo") or "fixo"
        if tipo not in ("fixo", "percentual"):
            raise ValueError("Escolha porcentagem ou valor fixo.")
        if valor < 0:
            raise ValueError("O valor pago pela prestadora não pode ser negativo.")
        if tipo == "percentual" and valor > 100:
            raise ValueError("A porcentagem não pode passar de 100.")
        if produto_id in vistos:
            raise ValueError("O mesmo produto ou serviço não pode entrar duas vezes.")
        vistos.add(produto_id)
        saida.append({"produto_servico_id": produto_id, "tipo": tipo, "valor": valor})
    return saida


def base_da_regra(preco, quantidade, tipo, valor) -> Decimal:
    """Quanto a prestadora paga neste item: porcentagem do preço ou valor fixo por unidade."""
    qtd = Decimal(str(quantidade or 0))
    numero = Decimal(str(valor or 0))
    if tipo == "percentual":
        return qtd * Decimal(str(preco or 0)) * numero / Decimal(100)
    return qtd * numero


def linhas_da_venda(conta, itens, mapa) -> list[tuple] | None:
    """Itens com a base que a prestadora paga. None quando a venda não tem essa regra."""
    if conta is None or not itens:
        return None
    escopo = getattr(conta, "comissao_escopo", None) or "especificos"
    if escopo == "todos":
        if getattr(conta, "comissao_valor", None) is None:
            return None
        tipo = getattr(conta, "comissao_tipo", None) or "percentual"
        return [
            (item, base_da_regra(item.preco_unitario, item.quantidade, tipo, conta.comissao_valor))
            for item in itens
        ]
    linhas = []
    for item in itens:
        regra = mapa.get((getattr(conta, "id", None), item.produto_servico_id))
        if regra is None:
            continue
        tipo, valor = regra
        linhas.append((item, base_da_regra(item.preco_unitario, item.quantidade, tipo, valor)))
    if not linhas:
        return None
    return linhas


def comissao_do_vendedor(valor_prestadora: Decimal, percentual) -> Decimal:
    """Parte do vendedor sobre o valor que a prestadora paga."""
    pct = Decimal(str(percentual or 0))
    return (Decimal(valor_prestadora) * pct / Decimal(100)).quantize(Decimal("0.01"))


def parte_comissao_item(base_prestadora, quantidade, regra, percentual_padrao) -> Decimal:
    """Parte do vendedor em um item.

    regra {"tipo": "fixo"|"percentual", "valor": Decimal} vem da categoria.
    Valor fixo é por unidade. Porcentagem incide sobre o valor pago pela prestadora.
    Sem regra na categoria, usa o percentual padrão do funcionário.
    """
    if regra and regra.get("tipo") == "fixo":
        return (Decimal(str(regra.get("valor") or 0)) * Decimal(str(quantidade or 0))).quantize(Decimal("0.01"))
    percentual = regra.get("valor") if regra else percentual_padrao
    return comissao_do_vendedor(Decimal(str(base_prestadora or 0)), percentual)


def validar_comissoes_categoria(itens) -> list[dict]:
    if itens is None:
        return []
    if not isinstance(itens, list):
        raise ValueError("Informe a comissão por categoria.")

    saida = []
    vistos = set()
    for item in itens:
        if not isinstance(item, dict):
            raise ValueError("Comissão de categoria inválida.")
        try:
            categoria_id = int(item.get("categoria_id"))
        except (TypeError, ValueError):
            raise ValueError("Escolha uma categoria.") from None
        bruto = item.get("valor")
        if bruto is None or str(bruto).strip() == "":
            continue
        tipo = item.get("tipo") or "percentual"
        if tipo not in ("fixo", "percentual"):
            raise ValueError("Escolha valor fixo ou porcentagem.")
        try:
            valor = Decimal(str(bruto).replace(",", ".")).quantize(Decimal("0.01"))
        except (InvalidOperation, TypeError):
            raise ValueError("Informe o valor da comissão.") from None
        if valor < 0:
            raise ValueError("A comissão não pode ser negativa.")
        if tipo == "percentual" and valor > 100:
            raise ValueError("A porcentagem não pode passar de 100.")
        if categoria_id in vistos:
            raise ValueError("A mesma categoria não pode entrar duas vezes.")
        vistos.add(categoria_id)
        saida.append({"categoria_id": categoria_id, "tipo": tipo, "valor": valor})
    return saida


def serializar_comissoes_vendedor(vendedor) -> list[dict]:
    linhas = []
    relacao = vendedor.comissoes_categoria.select_related("categoria").order_by(
        "categoria__ordem", "categoria__nome", "id",
    )
    for item in relacao:
        linhas.append({
            "categoria_id": item.categoria_id,
            "categoria_nome": item.categoria.nome if item.categoria_id else "",
            "tipo": item.tipo,
            "valor": f"{item.valor:.2f}",
        })
    return linhas


def aplicar_comissoes_vendedor(vendedor, itens) -> None:
    from .models import CategoriaProdutoServico, VendedorCategoriaComissao

    try:
        normalizados = validar_comissoes_categoria(itens or [])
    except ValueError as exc:
        raise ValidationError({"comissoes_categoria": str(exc)}) from exc

    ids = [item["categoria_id"] for item in normalizados]
    existentes = set(CategoriaProdutoServico.objects.filter(id__in=ids).values_list("id", flat=True))
    if len(existentes) != len(ids):
        raise ValidationError({"comissoes_categoria": "Há categoria que não está cadastrada."})

    VendedorCategoriaComissao.objects.filter(vendedor_id=vendedor.id).exclude(categoria_id__in=ids).delete()
    for item in normalizados:
        VendedorCategoriaComissao.objects.update_or_create(
            vendedor_id=vendedor.id,
            categoria_id=item["categoria_id"],
            defaults={"tipo": item["tipo"], "valor": item["valor"], "loja_id": vendedor.loja_id},
        )


def serializar_comissoes_conta(conta) -> list[dict]:
    linhas = []
    relacao = conta.comissoes_produtos.select_related(
        "produto_servico", "produto_servico__categoria",
    ).order_by("produto_servico__categoria__ordem", "produto_servico__nome", "id")
    for item in relacao:
        produto = item.produto_servico
        categoria = produto.categoria
        linhas.append({
            "produto_servico_id": produto.id,
            "tipo": item.tipo or "fixo",
            "valor": f"{item.valor:.2f}",
            "nome": produto.nome,
            "codigo": produto.codigo or "",
            "preco": f"{produto.preco:.2f}",
            "tipo": produto.tipo,
            "categoria_id": categoria.id if categoria else None,
            "categoria_nome": categoria.nome if categoria else "",
        })
    return linhas


def aplicar_comissoes_conta(conta, itens) -> None:
    from .models import ContaProdutoComissao, ProdutoServico

    if conta.tipo not in TIPOS_COM_COMISSAO:
        ContaProdutoComissao.objects.filter(conta_id=conta.id).delete()
        return

    try:
        normalizados = validar_itens_comissao(itens or [])
    except ValueError as exc:
        raise ValidationError({"comissoes": str(exc)}) from exc

    ids = [item["produto_servico_id"] for item in normalizados]
    existentes = set(ProdutoServico.objects.filter(id__in=ids).values_list("id", flat=True))
    if len(existentes) != len(ids):
        raise ValidationError({"comissoes": "Há produto ou serviço que não está no catálogo."})

    ContaProdutoComissao.objects.filter(conta_id=conta.id).exclude(produto_servico_id__in=ids).delete()
    for item in normalizados:
        ContaProdutoComissao.objects.update_or_create(
            conta_id=conta.id,
            produto_servico_id=item["produto_servico_id"],
            defaults={"valor": item["valor"], "tipo": item["tipo"], "loja_id": conta.loja_id},
        )


def _mapa_valores(conta_ids, produto_ids) -> dict[tuple[int, int], tuple[str, Decimal]]:
    from .models import ContaProdutoComissao

    if not conta_ids or not produto_ids:
        return {}
    return {
        (row.conta_id, row.produto_servico_id): (row.tipo or "fixo", row.valor)
        for row in ContaProdutoComissao.objects.filter(
            conta_id__in=conta_ids,
            produto_servico_id__in=produto_ids,
        )
    }


def valor_pago_pela_prestadora(oportunidade) -> Decimal | None:
    """Soma o que a prestadora paga nos itens da venda.

    None quando não há regra — a venda mantém o que já estava gravado.
    """
    if not oportunidade.empresa_prestadora_id:
        return None
    itens = list(oportunidade.itens.all())
    mapa = _mapa_valores(
        [oportunidade.empresa_prestadora_id],
        [item.produto_servico_id for item in itens],
    )
    linhas = linhas_da_venda(getattr(oportunidade, "empresa_prestadora", None), itens, mapa)
    if linhas is None:
        return None
    return sum((base for _, base in linhas), Decimal(0)).quantize(Decimal("0.01"))


def atualizar_valor_pago_pela_prestadora(oportunidade) -> None:
    """Grava na venda o que a prestadora paga. A parte do vendedor é o percentual do funcionário."""
    base = valor_pago_pela_prestadora(oportunidade)
    if base is None or oportunidade.valor_comissao == base:
        return
    oportunidade.valor_comissao = base
    oportunidade.save(update_fields=["valor_comissao", "updated_at"])


def gravar_comissoes_das_vendas(oportunidades) -> None:
    """Atualiza o valor gravado em cada venda com a regra atual da prestadora."""
    vendas = oportunidades.select_related("empresa_prestadora").prefetch_related("itens")
    for venda in vendas:
        atualizar_valor_pago_pela_prestadora(venda)


def atualizar_comissoes_da_prestadora(conta_id: int) -> None:
    """Recalcula as vendas dessa prestadora depois que a regra de comissão muda."""
    from .models import Oportunidade

    gravar_comissoes_das_vendas(
        Oportunidade.objects.filter(empresa_prestadora_id=conta_id),
    )


def _regras_categoria_vendedor(vendedor) -> tuple[Decimal, dict]:
    percentual = Decimal(str(getattr(vendedor, "comissao_padrao", 0) or 0))
    regras = {}
    relacao = getattr(vendedor, "comissoes_categoria", None)
    if relacao is None:
        return percentual, regras
    for row in relacao.all():
        regras[row.categoria_id] = {"tipo": row.tipo, "valor": row.valor}
    return percentual, regras


def _regra_da_categoria(categoria, regras):
    """Usa a regra da subpasta ou, se ela estiver em branco, a da categoria de cima."""
    atual = categoria
    for _ in range(6):
        if atual is None:
            return None
        regra = regras.get(getattr(atual, "id", None))
        if regra is not None:
            return regra
        atual = getattr(atual, "pai", None)
    return None


def partes_por_oportunidade(oportunidades, vendedor) -> dict[int, Decimal]:
    """Comissão do vendedor em cada venda.

    Com valor configurado na prestadora, usa a regra da categoria: valor fixo por unidade
    ou porcentagem. Categoria sem regra usa o percentual padrão do funcionário.
    Venda antiga, sem essa configuração, continua com o valor já gravado.
    """
    if vendedor is None:
        return {}
    percentual, regras = _regras_categoria_vendedor(vendedor)
    if hasattr(oportunidades, "prefetch_related"):
        ops = list(
            oportunidades.select_related("empresa_prestadora").prefetch_related(
                "itens__produto_servico__categoria__pai__pai",
            )
        )
    else:
        ops = list(oportunidades)
    if not ops:
        return {}
    conta_ids = [op.empresa_prestadora_id for op in ops if op.empresa_prestadora_id]
    produto_ids = [
        item.produto_servico_id
        for op in ops
        for item in op.itens.all()
    ]
    mapa = _mapa_valores(conta_ids, produto_ids)
    partes: dict[int, Decimal] = {}
    for op in ops:
        linhas = linhas_da_venda(getattr(op, "empresa_prestadora", None), list(op.itens.all()), mapa)
        if linhas is None:
            partes[op.id] = Decimal(op.valor_comissao or 0).quantize(Decimal("0.01"))
            continue
        parte = Decimal(0)
        for item, base in linhas:
            categoria = getattr(getattr(item, "produto_servico", None), "categoria", None)
            parte += parte_comissao_item(
                base,
                Decimal(item.quantidade or 0),
                _regra_da_categoria(categoria, regras),
                percentual,
            )
        partes[op.id] = parte.quantize(Decimal("0.01"))
    return partes


def comissao_exibida_vendedor(oportunidades, vendedor) -> Decimal:
    """Parte do vendedor na Home."""
    total = sum(partes_por_oportunidade(oportunidades, vendedor).values(), Decimal("0.00"))
    return total.quantize(Decimal("0.01"))


def mapa_comissao_dos_vendedores(oportunidades, somente_vendedor_id=None) -> dict[int, Decimal]:
    """Comissão de cada venda pela regra do vendedor.

    somente_vendedor_id limita o mapa a um vendedor. Os demais ficam de fora.
    """
    from .models import Vendedor

    if hasattr(oportunidades, "order_by"):
        vendedor_ids = list(oportunidades.order_by().values_list("vendedor_id", flat=True).distinct())
    else:
        vendedor_ids = list({getattr(op, "vendedor_id", None) for op in oportunidades})
    if somente_vendedor_id is not None:
        vendedor_ids = [vid for vid in vendedor_ids if vid == somente_vendedor_id]
    vendedores = {
        vendedor.id: vendedor
        for vendedor in Vendedor.objects.filter(
            id__in=[vid for vid in vendedor_ids if vid],
        ).prefetch_related("comissoes_categoria")
    }
    mapa: dict[int, Decimal] = {}
    for vid in vendedor_ids:
        vendedor = vendedores.get(vid)
        if vendedor is None:
            continue
        if hasattr(oportunidades, "filter"):
            dele = oportunidades.filter(vendedor_id=vid)
        else:
            dele = [op for op in oportunidades if getattr(op, "vendedor_id", None) == vid]
        mapa.update(partes_por_oportunidade(dele, vendedor))
    return mapa
