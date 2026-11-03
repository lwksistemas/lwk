"""Saldo por lote. Não reescreve quantidade_atual nem movimentações antigas."""
from __future__ import annotations

import re
from datetime import date
from decimal import Decimal


class BaixaLoteError(ValueError):
    """A saída pedida usaria saldo vencido, inativo ou acima do que pode sair."""


def _validade(lote) -> date | None:
    valor = lote.get("validade") if isinstance(lote, dict) else getattr(lote, "validade", None)
    if not valor:
        return None
    if isinstance(valor, date):
        return valor
    return date.fromisoformat(str(valor)[:10])


def _quantidade(lote) -> Decimal:
    bruto = lote.get("quantidade") if isinstance(lote, dict) else lote.quantidade
    return Decimal(str(bruto or "0"))


def classe_lote(lote, hoje: date) -> int:
    """0 válido com data, 1 sem validade, 2 vencido."""
    validade = _validade(lote)
    if validade is None:
        return 1
    if validade < hoje:
        return 2
    return 0


def quantidade_vencida(lotes, hoje: date | None = None) -> Decimal:
    hoje = hoje or date.today()
    return sum((_quantidade(lote) for lote in lotes if classe_lote(lote, hoje) == 2), Decimal("0"))


def resumo_saldos(quantidade_atual, lotes, *, ativo: bool = True, hoje: date | None = None) -> dict:
    """Total, o que pode sair e o que nunca entrou em lote.

    Lote com quantidade zero sai da conta. Vencido continua no total, fora do utilizável.
    """
    hoje = hoje or date.today()
    rastreados = [lote for lote in lotes if _quantidade(lote) > 0]
    em_lotes = sum((_quantidade(lote) for lote in rastreados), Decimal("0"))
    sem_lote = Decimal(str(quantidade_atual)) - em_lotes
    if sem_lote < 0:
        sem_lote = Decimal("0")
    return {
        "total": Decimal(str(quantidade_atual)),
        "utilizavel": saldo_utilizavel(quantidade_atual, rastreados, ativo=ativo, hoje=hoje),
        "sem_lote": sem_lote,
        "em_lotes": em_lotes,
    }


def saldo_utilizavel(quantidade_atual, lotes, *, ativo: bool = True, hoje: date | None = None) -> Decimal:
    """Saldo que pode sair: o total menos o que está só em lote vencido.

    O saldo antigo sem lote continua nesse número. Lote vencido não entra.
    Produto inativo não sai.
    """
    if not ativo:
        return Decimal("0")
    hoje = hoje or date.today()
    livre = Decimal(str(quantidade_atual)) - quantidade_vencida(lotes, hoje)
    return livre if livre > 0 else Decimal("0")


def consumir_lotes(lotes: list[dict], quantidade: Decimal, hoje: date | None = None) -> list[dict]:
    """Baixa o lote válido que vence antes. Sem validade só depois. Vencido não sai."""
    hoje = hoje or date.today()
    restante = quantidade if quantidade > 0 else Decimal("0")
    ordenados = sorted(
        lotes,
        key=lambda lote: (classe_lote(lote, hoje), _validade(lote) or date.max, lote.get("id") or 0),
    )
    saida = []
    for lote in ordenados:
        atual = _quantidade(lote)
        pode = classe_lote(lote, hoje) < 2 and restante > 0
        toma = min(atual, restante) if pode else Decimal("0")
        novo = dict(lote)
        novo["quantidade"] = atual - toma
        restante -= toma
        saida.append(novo)
    return saida


def registrar_entrada_lote(produto, item: dict, quantidade: Decimal, validade) -> None:
    from .models import LoteProdutoEstoque

    codigo = (item.get("lote") or "").strip()[:50]
    if not codigo and not validade:
        return
    if quantidade <= 0:
        return
    documento = re.sub(r"\D", "", item.get("documento_fornecedor") or "")[:20]
    lote = LoteProdutoEstoque.objects.filter(produto=produto, codigo=codigo, validade=validade).first()
    if lote is None:
        lote = LoteProdutoEstoque(produto=produto, codigo=codigo, validade=validade, quantidade=Decimal("0"))
    lote.quantidade = (lote.quantidade or Decimal("0")) + quantidade
    lote.documento = documento
    lote.fornecedor_nome = (item.get("fornecedor") or "")[:200]
    lote.numero_nota = (item.get("numero_nota") or "")[:20]
    lote.chave = (item.get("chave") or "")[:44]
    lote.save()


def abater_lotes(produto, quantidade: Decimal, hoje: date | None = None) -> None:
    """Chamar depois de reduzir quantidade_atual, dentro da mesma transação.

    O saldo anterior à saída é quantidade_atual + quantidade.
    """
    from .models import LoteProdutoEstoque

    if quantidade <= 0:
        return
    hoje = hoje or date.today()
    nome = getattr(produto, "nome", "Produto")
    if not getattr(produto, "is_active", True):
        raise BaixaLoteError(f"{nome} está inativo. A saída não foi registrada.")
    linhas = list(
        LoteProdutoEstoque.objects.select_for_update()
        .filter(produto=produto, quantidade__gt=0)
        .order_by("id"),
    )
    lotes = [{"id": linha.id, "quantidade": linha.quantidade, "validade": linha.validade} for linha in linhas]
    antes = Decimal(str(produto.quantidade_atual)) + quantidade
    util = saldo_utilizavel(antes, lotes, ativo=True, hoje=hoje)
    if quantidade > util:
        raise BaixaLoteError(
            f"{nome} não tem saldo utilizável para esta saída. "
            f"Disponível: {util}. Lote vencido não é baixado.",
        )
    if not linhas:
        return
    ajustados = consumir_lotes(lotes, quantidade, hoje)
    por_id = {item["id"]: item["quantidade"] for item in ajustados}
    for linha in linhas:
        nova = por_id.get(linha.id)
        if nova is None or nova == linha.quantidade:
            continue
        linha.quantidade = nova
        linha.save(update_fields=["quantidade", "updated_at"])


def registrar_compra(item: dict, produto, fator: Decimal, quantidade: Decimal, custo: Decimal, validade, usuario: str) -> None:
    from .models import CompraFornecedorEstoque

    documento = re.sub(r"\D", "", item.get("documento_fornecedor") or "")[:20]
    data = None
    bruto = str(item.get("data_emissao") or "")[:10]
    if bruto:
        try:
            data = date.fromisoformat(bruto)
        except ValueError:
            data = None
    CompraFornecedorEstoque.objects.create(
        produto=produto,
        documento=documento,
        fornecedor_nome=(item.get("fornecedor") or "")[:200],
        codigo=(item.get("codigo_produto") or "")[:60],
        chave=(item.get("chave") or "")[:44],
        numero_nota=(item.get("numero_nota") or "")[:20],
        data_compra=data,
        quantidade=Decimal(str(item.get("quantidade") or "0")),
        unidade=(item.get("unidade_medida") or "")[:30],
        quantidade_estoque=quantidade,
        unidade_estoque=(item.get("unidade_estoque") or item.get("unidade_medida") or "")[:30],
        fator=fator,
        custo_unitario=custo,
        lote=(item.get("lote") or "")[:50],
        validade=validade,
        usuario=(usuario or "")[:80],
    )
