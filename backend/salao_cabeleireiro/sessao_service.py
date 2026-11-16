"""Abertura, sangria, suprimento e fechamento. O autônomo não precisa abrir o caixa todo dia."""
from decimal import Decimal

from django.utils import timezone

from .caixa_service import quantia
from .estoque_service import gravar


def nome_do_operador(user, loja) -> str:
    """O salão fica no cabeçalho. O operador é a pessoa que entrou, não o nome da loja."""
    completo = (user.get_full_name() or "").strip()
    loja_nome = (getattr(loja, "nome", "") or "").strip()
    if completo and completo.casefold() != loja_nome.casefold():
        return completo[:160]
    return (user.get_username() or "Caixa")[:160]


def precisa_abrir_caixa(modelo: str, sessao_aberta: bool) -> str | None:
    if modelo == "recepcionista" and not sessao_aberta:
        return "Abra o caixa antes de receber."
    return None


def saldo_esperado(saldo_inicial, dinheiro, suprimentos, sangrias) -> Decimal:
    return quantia(saldo_inicial) + quantia(dinheiro) + quantia(suprimentos) - quantia(sangrias)


def diferenca_caixa(contado, esperado) -> Decimal:
    return quantia(contado) - quantia(esperado)


def texto_estorno(venda) -> str:
    if not venda.itens.exists():
        return "Sem produto nesta operação"
    if venda.estoque_estornado or not venda.itens.filter(estoque_baixado=True).exists():
        return "Estoque devolvido"
    return "Estoque pendente de devolução"


def aplicar_cancelamento(venda, operador: str, motivo: str) -> None:
    """Guarda quem cancelou e o motivo. O valor original permanece no comprovante."""
    texto = (motivo or "").strip()
    if len(texto) < 3:
        raise ValueError("Informe o motivo do cancelamento.")
    venda.cancelado_em = timezone.now()
    venda.cancelado_por = (operador or "")[:160]
    venda.motivo_cancelamento = texto[:200]
    venda.estoque_estornado = venda.itens.exists() and not venda.itens.filter(estoque_baixado=True).exists()
    comprovante = dict(venda.comprovante or {})
    comprovante["cancelado"] = True
    comprovante["cancelado_em"] = timezone.localtime(venda.cancelado_em).strftime("%d/%m/%Y às %H:%M")
    comprovante["cancelado_por"] = venda.cancelado_por
    comprovante["motivo"] = venda.motivo_cancelamento
    comprovante["estorno"] = texto_estorno(venda)
    venda.comprovante = comprovante
    venda.save(update_fields=[
        "cancelado_em",
        "cancelado_por",
        "motivo_cancelamento",
        "estoque_estornado",
        "comprovante",
    ])


def _dinheiro_recebido(sessao) -> Decimal:
    total = Decimal("0")
    for venda in sessao.vendas.filter(is_active=True):
        for parte in venda.partes or []:
            if isinstance(parte, dict) and parte.get("forma") == "dinheiro":
                total += quantia(parte.get("valor"))
    return total


def _movimentos(sessao) -> tuple[Decimal, Decimal]:
    suprimentos = Decimal("0")
    sangrias = Decimal("0")
    for item in sessao.movimentos.all():
        if item.tipo == "suprimento":
            suprimentos += quantia(item.valor)
        elif item.tipo == "sangria":
            sangrias += quantia(item.valor)
    return suprimentos, sangrias


def resumo_sessao(sessao) -> dict:
    dinheiro = _dinheiro_recebido(sessao)
    suprimentos, sangrias = _movimentos(sessao)
    esperado = saldo_esperado(sessao.saldo_inicial, dinheiro, suprimentos, sangrias)
    return {
        "id": sessao.id,
        "operador": sessao.operador_nome,
        "aberta_em": timezone.localtime(sessao.aberta_em).strftime("%d/%m/%Y %H:%M"),
        "saldo_inicial": f"{quantia(sessao.saldo_inicial):.2f}",
        "dinheiro": f"{dinheiro:.2f}",
        "suprimentos": f"{suprimentos:.2f}",
        "sangrias": f"{sangrias:.2f}",
        "esperado": f"{esperado:.2f}",
        "fechada_em": timezone.localtime(sessao.fechada_em).strftime("%d/%m/%Y %H:%M") if sessao.fechada_em else "",
        "operador_fechamento": sessao.operador_fechamento,
        "dinheiro_contado": "" if sessao.dinheiro_contado is None else f"{quantia(sessao.dinheiro_contado):.2f}",
        "diferenca": "" if sessao.diferenca is None else f"{quantia(sessao.diferenca):.2f}",
        "observacao": sessao.observacao,
        "aberta": sessao.is_active,
    }


def sessao_aberta():
    from .models import SessaoCaixa

    return SessaoCaixa.objects.filter(is_active=True).order_by("-id").first()


def abrir_caixa(operador: str, saldo_inicial) -> dict:
    from .models import SessaoCaixa

    if sessao_aberta() is not None:
        raise ValueError("O caixa já está aberto.")
    saldo = quantia(saldo_inicial)
    if saldo < 0:
        raise ValueError("O saldo inicial não pode ser negativo.")
    sessao = gravar(SessaoCaixa, operador_nome=(operador or "")[:160], saldo_inicial=saldo)
    return resumo_sessao(sessao)


def lancar_movimento(operador: str, tipo: str, valor, motivo: str) -> dict:
    from .models import MovimentoCaixa

    sessao = sessao_aberta()
    if sessao is None:
        raise ValueError("Abra o caixa antes de lançar sangria ou suprimento.")
    if tipo not in {"sangria", "suprimento"}:
        raise ValueError("Escolha sangria ou suprimento.")
    quantia_valor = quantia(valor)
    if quantia_valor <= 0:
        raise ValueError("Informe um valor maior que zero.")
    texto = (motivo or "").strip()
    if len(texto) < 3:
        raise ValueError("Informe o motivo da movimentação.")
    if tipo == "sangria":
        atual = resumo_sessao(sessao)
        if quantia_valor > quantia(atual["esperado"]):
            raise ValueError("A sangria não pode passar do dinheiro esperado na gaveta.")
    gravar(
        MovimentoCaixa,
        sessao=sessao,
        tipo=tipo,
        valor=quantia_valor,
        motivo=texto[:200],
        operador_nome=(operador or "")[:160],
    )
    return resumo_sessao(sessao)


def fechar_caixa(operador: str, dinheiro_contado, observacao: str = "") -> dict:
    sessao = sessao_aberta()
    if sessao is None:
        raise ValueError("Não há caixa aberto.")
    contado = quantia(dinheiro_contado)
    if contado < 0:
        raise ValueError("O dinheiro contado não pode ser negativo.")
    atual = resumo_sessao(sessao)
    sessao.is_active = False
    sessao.fechada_em = timezone.now()
    sessao.operador_fechamento = (operador or "")[:160]
    sessao.dinheiro_contado = contado
    sessao.diferenca = diferenca_caixa(contado, atual["esperado"])
    sessao.observacao = (observacao or "")[:200]
    sessao.save(update_fields=[
        "is_active",
        "fechada_em",
        "operador_fechamento",
        "dinheiro_contado",
        "diferenca",
        "observacao",
    ])
    return resumo_sessao(sessao)


def painel_caixa(modelo: str) -> dict:
    from .models import SessaoCaixa

    aberta = sessao_aberta()
    historico = [
        resumo_sessao(item)
        for item in SessaoCaixa.objects.filter(is_active=False).order_by("-fechada_em", "-id")[:12]
    ]
    return {
        "modelo": modelo,
        "exige_abertura": modelo == "recepcionista",
        "aberta": resumo_sessao(aberta) if aberta is not None else None,
        "historico": historico,
    }
