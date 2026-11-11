"""Venda de produto. O insumo do procedimento não passa por aqui."""
from __future__ import annotations

from decimal import Decimal


class VendaProdutoError(ValueError):
    """A venda pedida não pode sair do estoque nem entrar no recibo."""


def subtotal_item(quantidade, preco_unitario, desconto) -> Decimal:
    """Quantidade vezes o preço, menos o desconto da linha. Nunca negativo."""
    bruto = Decimal(str(quantidade or 0)) * Decimal(str(preco_unitario or 0))
    liquido = bruto - Decimal(str(desconto or 0))
    return liquido if liquido > 0 else Decimal("0")


def validar_item_venda(produto, quantidade, lotes, *, hoje=None) -> None:
    """Produto inativo, sem permissão de venda ou sem saldo utilizável não sai."""
    from .estoque_lotes import saldo_utilizavel

    if not getattr(produto, "is_active", True):
        raise VendaProdutoError(f"{produto.nome} está inativo.")
    if not getattr(produto, "vende_ao_cliente", False):
        raise VendaProdutoError(f"{produto.nome} não está liberado para venda.")
    qtd = Decimal(str(quantidade or 0))
    if qtd <= 0:
        raise VendaProdutoError("Quantidade deve ser maior que zero.")
    preco = Decimal(str(getattr(produto, "preco_venda", 0) or 0))
    if preco < 0:
        raise VendaProdutoError("Preço de venda inválido.")
    livre = saldo_utilizavel(
        getattr(produto, "quantidade_atual", 0),
        lotes,
        ativo=True,
        hoje=hoje,
    )
    if qtd > livre:
        raise VendaProdutoError(
            f"Saldo utilizável de {produto.nome} é {livre}. Lote vencido não entra nessa conta.",
        )


def nome_exibicao_venda(venda) -> str:
    """Nome do recibo. Sem cadastro e sem nome, fica o consumidor não identificado."""
    paciente = getattr(venda, "paciente", None)
    nome_paciente = (getattr(paciente, "nome", "") or "").strip() if paciente is not None else ""
    if nome_paciente:
        return nome_paciente
    nome = (getattr(venda, "nome_cliente", "") or "").strip()
    return nome or "Consumidor não identificado"


def pessoa_recibo(venda):
    """Quem recebe o cupom. Pode ser o cadastro ou só o nome digitado no caixa."""
    from types import SimpleNamespace

    paciente = getattr(venda, "paciente", None)
    if paciente is not None:
        return paciente
    return SimpleNamespace(
        nome=nome_exibicao_venda(venda),
        cpf="",
        email=(getattr(venda, "email_cliente", "") or "").strip(),
        telefone=(getattr(venda, "telefone_cliente", "") or "").strip(),
    )


def linha_recibo(nome: str, quantidade, preco_unitario, desconto) -> dict:
    qtd = Decimal(str(quantidade or 0))
    preco = Decimal(str(preco_unitario or 0))
    desc = Decimal(str(desconto or 0))
    quantidade_texto = f"{qtd:.2f}".rstrip("0").rstrip(".")
    return {
        "nome": nome,
        "quantidade": quantidade_texto or "0",
        "preco_unitario": float(preco),
        "desconto": float(desc),
        "subtotal": float(subtotal_item(qtd, preco, desc)),
    }


def total_vendas_consulta(consulta) -> Decimal:
    """Soma só o que foi vendido. Uso no procedimento fica de fora e vale zero."""
    from .models import ConsultaProdutoUtilizado

    total = Decimal("0")
    itens = ConsultaProdutoUtilizado.objects.filter(
        consulta=consulta, finalidade="venda", estornado=False,
    )
    for item in itens:
        total += subtotal_item(item.quantidade, item.preco_unitario, item.desconto)
    return total


def produtos_da_consulta(consulta) -> list[dict]:
    from .models import ConsultaProdutoUtilizado

    linhas = []
    itens = (
        ConsultaProdutoUtilizado.objects.filter(consulta=consulta, finalidade="venda", estornado=False)
        .select_related("produto")
    )
    for item in itens:
        linhas.append(linha_recibo(item.produto.nome, item.quantidade, item.preco_unitario, item.desconto))
    return linhas


def produtos_da_venda(venda) -> list[dict]:
    linhas = []
    for item in venda.itens.select_related("produto").all():
        if item.estornado:
            continue
        linhas.append(linha_recibo(item.produto.nome, item.quantidade, item.preco_unitario, item.desconto))
    return linhas


def produtos_do_pagamento(payment) -> list[dict]:
    venda = getattr(payment, "venda_balcao", None)
    if venda is not None and venda.status != "cancelada":
        return produtos_da_venda(venda)
    appointment = getattr(payment, "appointment", None)
    consulta = getattr(appointment, "consulta", None) if appointment is not None else None
    if consulta is None:
        return []
    return produtos_da_consulta(consulta)


def _lotes_do_produto(produto) -> list[dict]:
    from .models import LoteProdutoEstoque

    return [
        {"quantidade": lote.quantidade, "validade": lote.validade}
        for lote in LoteProdutoEstoque.objects.filter(produto=produto, quantidade__gt=0)
    ]


def _normalizar_nome(valor: str) -> str:
    return " ".join(str(valor or "").casefold().split())


def usuario_pode_fechar_caixa(sessao, usuario) -> bool:
    """Só o operador escolhido na abertura fecha a gaveta."""
    if sessao is None or usuario is None or not getattr(usuario, "is_authenticated", False):
        return False
    _, nome_login = _nome_usuario(usuario)
    if _normalizar_nome(nome_login) and _normalizar_nome(nome_login) == _normalizar_nome(nome_operador_caixa(sessao)):
        return True
    email = (getattr(usuario, "email", "") or "").strip().casefold()
    responsavel_id = getattr(sessao, "responsavel_id", None)
    if not email or not responsavel_id:
        return False
    from .models import Professional

    pessoa = Professional.objects.filter(pk=responsavel_id).only("email").first()
    return bool(pessoa is not None and (pessoa.email or "").strip().casefold() == email)


def _nome_usuario(usuario) -> tuple[int | None, str]:
    if usuario is None or not getattr(usuario, "is_authenticated", False):
        return None, ""
    nome = ""
    obter = getattr(usuario, "get_full_name", None)
    if callable(obter):
        nome = (obter() or "").strip()
    if not nome:
        nome = (getattr(usuario, "username", "") or "").strip()
    return getattr(usuario, "pk", None), nome


def totais_gaveta(sessao) -> dict:
    """Soma as vendas desta gaveta, aberta ou já fechada."""
    from decimal import Decimal

    vendas = Decimal("0")
    recebido = Decimal("0")
    a_receber = Decimal("0")
    if sessao is None:
        return {"vendas_produtos": 0.0, "recebido": 0.0, "a_receber": 0.0}
    for venda in sessao.vendas.select_related("payment").exclude(status="cancelada"):
        payment = venda.payment
        if payment is None or payment.status == "CANCELLED":
            continue
        vendas += Decimal(str(payment.valor_produtos or 0))
        total = Decimal(str(payment.valor_total if payment.valor_total is not None else payment.amount or 0))
        if payment.status == "PAID":
            recebido += Decimal(str(payment.amount or 0))
            continue
        pago = Decimal(str(payment.amount or 0))
        if total > pago:
            a_receber += total - pago
    return {
        "vendas_produtos": float(vendas),
        "recebido": float(recebido),
        "a_receber": float(a_receber),
    }


def totais_sessao_caixa(sessao) -> dict:
    """Soma só a gaveta aberta. Caixa fechado não leva valor para o próximo operador."""
    if sessao is None or getattr(sessao, "status", "") != "aberta":
        return {"vendas_produtos": 0.0, "recebido": 0.0, "a_receber": 0.0}
    return totais_gaveta(sessao)


def nome_operador_caixa(sessao) -> str:
    """O mesmo nome da página do caixa: o funcionário escolhido ao abrir."""
    if sessao is None:
        return ""
    return (getattr(sessao, "responsavel_nome", "") or getattr(sessao, "operador_nome", "") or "").strip()


def nome_operador_pagamento(payment) -> str:
    """Venda de produto já guarda o operador do caixa. Atendimento usa o nome gravado no recebimento."""
    venda = getattr(payment, "venda_balcao", None)
    if venda is not None:
        nome = (getattr(venda, "operador_nome", "") or "").strip()
        if nome:
            return nome
    return (getattr(payment, "operador_nome", "") or "").strip()


def gravar_operador_do_caixa(payment) -> None:
    """Copia o operador da gaveta aberta. Não troca um nome que já foi gravado."""
    if payment is None or (getattr(payment, "operador_nome", "") or "").strip():
        return
    sessao = sessao_caixa_aberta(getattr(payment, "loja_id", None))
    nome = nome_operador_caixa(sessao)
    if not nome:
        return
    payment.operador_nome = nome[:150]
    payment.operador_id = getattr(sessao, "responsavel_id", None) or getattr(sessao, "operador_id", None)
    payment.save(update_fields=["operador_nome", "operador_id", "updated_at"])


def _nome_profissional(consulta) -> tuple[int | None, str]:
    if consulta is None:
        return None, ""
    prof = getattr(consulta, "professional", None)
    if prof is None and getattr(consulta, "professional_id", None):
        from .models import Professional

        prof = Professional.objects.filter(pk=consulta.professional_id).only("nome").first()
    if prof is None:
        return None, ""
    return getattr(prof, "pk", None), (getattr(prof, "nome", "") or "").strip()


def gravar_quem_recebeu(payment, *, origem: str = "", consulta=None, usuario=None) -> None:
    """PDV grava o caixa. Consulta grava o profissional. Financeiro grava quem confirmou."""
    if payment is None or (getattr(payment, "operador_nome", "") or "").strip():
        return
    if (origem or "").strip().lower() == "pdv":
        gravar_operador_do_caixa(payment)
        return
    if (origem or "").strip().lower() == "financeiro":
        pessoa_id, nome = _nome_usuario(usuario)
    else:
        pessoa_id, nome = _nome_profissional(consulta)
        if not nome:
            pessoa_id, nome = _nome_usuario(usuario)
    nome = (nome or "").strip()
    if not nome:
        return
    payment.operador_nome = nome[:150]
    payment.operador_id = pessoa_id
    payment.save(update_fields=["operador_nome", "operador_id", "updated_at"])


def fechamento_automatico(aberta_em, agora):
    """23:59 do dia da abertura, depois que esse dia já acabou."""
    from datetime import datetime, time
    from zoneinfo import ZoneInfo

    if aberta_em is None or agora is None:
        return None
    fuso = ZoneInfo("America/Sao_Paulo")
    abertura = aberta_em.astimezone(fuso)
    momento = agora.astimezone(fuso)
    if momento.date() <= abertura.date():
        return None
    return datetime.combine(abertura.date(), time(23, 59, 59), tzinfo=fuso)


def fechar_caixas_esquecidos_da_loja(loja_id, agora=None) -> int:
    from django.utils import timezone

    from .models import SessaoCaixa

    momento = agora or timezone.now()
    fechados = 0
    abertas = SessaoCaixa.objects.filter(loja_id=loja_id, status=SessaoCaixa.STATUS_ABERTA)
    for sessao in abertas:
        limite = fechamento_automatico(sessao.aberta_em, momento)
        if limite is None:
            continue
        sessao.status = SessaoCaixa.STATUS_FECHADA
        sessao.fechada_em = limite
        sessao.save(update_fields=["status", "fechada_em"])
        fechados += 1
    return fechados


def fechar_caixas_esquecidos() -> int:
    """Job do worker: fecha a gaveta que passou das 23:59."""
    from core.db_config import ensure_loja_database_config
    from tenants.middleware import set_current_loja_id, set_current_tenant_db

    from .catalogo_service import lojas_clinica_beleza_com_schema

    total = 0
    for loja in lojas_clinica_beleza_com_schema(apenas_ativas=True):
        if not ensure_loja_database_config(loja.database_name, conn_max_age=0):
            continue
        try:
            set_current_loja_id(loja.id)
            set_current_tenant_db(loja.database_name)
            total += fechar_caixas_esquecidos_da_loja(loja.id)
        except Exception:
            import logging

            logging.getLogger(__name__).exception("Fechamento automático do caixa, loja %s", loja.id)
        finally:
            set_current_loja_id(None)
            set_current_tenant_db("default")
    return total


def sessao_caixa_aberta(loja_id):
    from .models import SessaoCaixa

    fechar_caixas_esquecidos_da_loja(loja_id)
    return (
        SessaoCaixa.objects.filter(loja_id=loja_id, status=SessaoCaixa.STATUS_ABERTA)
        .order_by("-id")
        .first()
    )


def funcionarios_do_caixa(loja_id) -> list[dict]:
    from .models import Professional

    return [
        {"id": pessoa.id, "nome": pessoa.nome}
        for pessoa in Professional.objects.filter(loja_id=loja_id, is_active=True).order_by("nome")
    ]


def abrir_caixa(loja_id, usuario, *, nome: str = "", responsavel_id=None):
    from .models import Professional, SessaoCaixa

    aberta = sessao_caixa_aberta(loja_id)
    if aberta is not None:
        return aberta
    nome_caixa = (nome or "Recepção").strip()[:80] or "Recepção"
    pessoa = Professional.objects.filter(pk=responsavel_id, loja_id=loja_id, is_active=True).first()
    if pessoa is None:
        raise VendaProdutoError("Escolha um funcionário cadastrado.")
    operador_id, _operador_login = _nome_usuario(usuario)
    responsavel = (pessoa.nome or "").strip()[:150]
    return SessaoCaixa.objects.create(
        loja_id=loja_id,
        nome=nome_caixa,
        responsavel_id=pessoa.id,
        responsavel_nome=responsavel,
        operador_id=operador_id,
        operador_nome=responsavel,
        status=SessaoCaixa.STATUS_ABERTA,
    )


def fechar_caixa(loja_id, usuario=None):
    from django.utils.timezone import now

    from .models import SessaoCaixa

    aberta = sessao_caixa_aberta(loja_id)
    if aberta is None:
        return None
    if not usuario_pode_fechar_caixa(aberta, usuario):
        nome = nome_operador_caixa(aberta) or "quem abriu"
        raise VendaProdutoError(f"Só {nome} pode fechar este caixa.")
    aberta.status = SessaoCaixa.STATUS_FECHADA
    aberta.fechada_em = now()
    aberta.save(update_fields=["status", "fechada_em"])
    return aberta


def registrar_venda_balcao(
    *,
    loja_id,
    paciente,
    itens: list[dict],
    payment_method: str,
    nome_cliente: str = "",
    telefone_cliente: str = "",
    email_cliente: str = "",
    usuario=None,
    chave: str = "",
):
    """Cria a venda, o pagamento e a baixa numa transação só."""
    from django.db import IntegrityError
    from django.utils.timezone import now

    from .estoque_service import movimentar_saida, tenant_atomic
    from .models import Patient, Payment, ProdutoEstoque, VendaBalcao, VendaBalcaoItem

    if not itens:
        raise VendaProdutoError("Informe ao menos um produto.")
    metodo = (payment_method or "CASH").strip().upper()
    metodos = {codigo for codigo, _rotulo in Payment.PAYMENT_METHOD_CHOICES}
    if metodo not in metodos or metodo == "DESPESA":
        raise VendaProdutoError("Forma de pagamento inválida.")
    chave = (chave or "").strip()[:64]

    with tenant_atomic():
        if chave:
            repetida = (
                VendaBalcao.objects.select_related("payment")
                .filter(loja_id=loja_id, chave=chave)
                .first()
            )
            if repetida is not None:
                return repetida
        sessao = sessao_caixa_aberta(loja_id)
        if sessao is None:
            raise VendaProdutoError("Abra o caixa para registrar a venda.")
        cliente = None
        if paciente not in (None, ""):
            cliente = Patient.objects.filter(pk=paciente, loja_id=loja_id).first()
            if cliente is None:
                raise VendaProdutoError("Cliente não encontrado nesta clínica.")
        nome = (nome_cliente or "").strip()[:200]
        if cliente is not None and not nome:
            nome = (cliente.nome or "").strip()[:200]
        preparados = []
        total = Decimal("0")
        ja_pedido: dict[int, Decimal] = {}
        for bruto in itens:
            produto = ProdutoEstoque.objects.select_for_update().filter(
                pk=bruto.get("produto"), loja_id=loja_id,
            ).first()
            if produto is None:
                raise VendaProdutoError("Produto não encontrado nesta clínica.")
            quantidade = Decimal(str(bruto.get("quantidade") or 0))
            preco = Decimal(str(bruto.get("preco_unitario") if bruto.get("preco_unitario") not in (None, "") else produto.preco_venda or 0))
            desconto = Decimal(str(bruto.get("desconto") or 0))
            if desconto < 0 or preco < 0:
                raise VendaProdutoError("Preço e desconto não podem ser negativos.")
            acumulado = ja_pedido.get(produto.pk, Decimal("0")) + quantidade
            validar_item_venda(produto, acumulado, _lotes_do_produto(produto))
            ja_pedido[produto.pk] = acumulado
            if desconto > preco * quantidade:
                raise VendaProdutoError(f"Desconto maior que o valor de {produto.nome}.")
            preparados.append((produto, quantidade, preco, desconto))
            total += subtotal_item(quantidade, preco, desconto)
        if total <= 0:
            raise VendaProdutoError("O total da venda precisa ser maior que zero.")

        operador_id = getattr(sessao, "responsavel_id", None)
        operador_nome = (getattr(sessao, "responsavel_nome", "") or "").strip()
        if not operador_nome:
            operador_id, operador_nome = _nome_usuario(usuario)
        from django.db import transaction

        try:
            with transaction.atomic():
                payment = Payment.objects.create(
                    appointment=None,
                    amount=total if metodo != "PRAZO" else Decimal("0"),
                    valor_total=total,
                    valor_produtos=total,
                    payment_method=metodo,
                    status="PENDING" if metodo == "PRAZO" else "PAID",
                    payment_date=None if metodo == "PRAZO" else now(),
                    loja_id=loja_id,
                    notes="Venda de produtos. Recibo comercial, não é nota fiscal.",
                )
                venda = VendaBalcao.objects.create(
                    paciente=cliente,
                    nome_cliente=nome,
                    telefone_cliente=(telefone_cliente or "").strip()[:30],
                    email_cliente=(email_cliente or "").strip()[:200],
                    operador_id=operador_id,
                    operador_nome=operador_nome,
                    chave=chave,
                    sessao=sessao,
                    payment=payment,
                    status=VendaBalcao.STATUS_CONCLUIDA,
                    loja_id=loja_id,
                )
        except IntegrityError:
            existente = VendaBalcao.objects.select_related("payment").filter(loja_id=loja_id, chave=chave).first()
            if existente is not None:
                return existente
            raise
        for produto, quantidade, preco, desconto in preparados:
            item = VendaBalcaoItem.objects.create(
                venda=venda,
                produto=produto,
                quantidade=quantidade,
                preco_unitario=preco,
                desconto=desconto,
                loja_id=loja_id,
            )
            movimentar_saida(
                produto,
                quantidade,
                motivo=f"Venda de produto #{venda.id}",
            )
            item.estoque_baixado = True
            item.save(update_fields=["estoque_baixado"])
        return venda


def cancelar_venda_balcao(venda) -> None:
    """Devolve a quantidade ao saldo e cancela o pagamento. O histórico das duas movimentações fica."""
    from .estoque_movimentacao_service import registrar_movimentacao
    from .estoque_service import tenant_atomic
    from .models import VendaBalcao

    if venda.status == VendaBalcao.STATUS_CANCELADA:
        raise VendaProdutoError("Esta venda já foi cancelada.")
    with tenant_atomic():
        for item in venda.itens.select_related("produto"):
            if item.estornado or not item.estoque_baixado:
                continue
            registrar_movimentacao(
                item.produto,
                "entrada",
                item.quantidade,
                motivo=f"Estorno da venda #{venda.id}",
            )
            item.estornado = True
            item.save(update_fields=["estornado"])
        venda.status = VendaBalcao.STATUS_CANCELADA
        venda.save(update_fields=["status"])
        payment = venda.payment
        if payment is not None and payment.status != "CANCELLED":
            payment.status = "CANCELLED"
            payment.save(update_fields=["status", "updated_at"])


def estornar_vendas_da_consulta(consulta) -> None:
    """Devolve só o produto vendido. O insumo usado no procedimento permanece baixado."""
    from .estoque_movimentacao_service import registrar_movimentacao
    from .models import ConsultaProdutoUtilizado

    itens = ConsultaProdutoUtilizado.objects.filter(
        consulta=consulta, finalidade="venda", estoque_baixado=True, estornado=False,
    ).select_related("produto")
    for item in itens:
        registrar_movimentacao(
            item.produto,
            "entrada",
            item.quantidade,
            motivo=f"Estorno da venda na consulta #{consulta.id}",
        )
        item.estornado = True
        item.save(update_fields=["estornado"])
