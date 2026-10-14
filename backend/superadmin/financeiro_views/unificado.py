"""Painel financeiro unificado (superadmin)."""
import logging

from django.db import models
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import FinanceiroLoja, PagamentoLoja

logger = logging.getLogger(__name__)

def _financeiro_unificado_stats():
    """Estatísticas unificadas (Asaas + Mercado Pago) para superadmin."""
    from decimal import Decimal

    from django.db.models import Sum

    from asaas_integration.models import AsaasPayment, LojaAssinatura

    # Asaas (AsaasPayment local)
    total_asaas = LojaAssinatura.objects.count()
    ativas_asaas = LojaAssinatura.objects.filter(ativa=True).count()
    pag_asaas = AsaasPayment.objects
    pagos_asaas_count = pag_asaas.filter(status__in=["RECEIVED", "CONFIRMED", "RECEIVED_IN_CASH"]).count()
    vencidos_asaas = pag_asaas.filter(status="OVERDUE").count()
    receita_asaas = pag_asaas.filter(status__in=["RECEIVED", "CONFIRMED", "RECEIVED_IN_CASH"]).aggregate(t=Sum("value"))["t"] or Decimal(0)
    pendente_asaas = pag_asaas.filter(status__in=["PENDING", "OVERDUE"]).aggregate(t=Sum("value"))["t"] or Decimal(0)
    pendentes_asaas_count = pag_asaas.filter(status="PENDING").count()

    # PagamentoLoja pagos que não estão no AsaasPayment (pagamentos antigos)
    asaas_ids_locais = set(pag_asaas.values_list("asaas_id", flat=True))
    pl_pagos = PagamentoLoja.objects.filter(status="pago").exclude(asaas_payment_id__in=asaas_ids_locais)
    receita_pl = pl_pagos.aggregate(t=Sum("valor"))["t"] or Decimal(0)
    pagos_pl_count = pl_pagos.count()

    # Mercado Pago (FinanceiroLoja com boleto MP)
    mp_fin = FinanceiroLoja.objects.filter(provedor_boleto="mercadopago", mercadopago_payment_id__isnull=False).exclude(mercadopago_payment_id="")
    total_mp = mp_fin.count()
    pendente_mp = sum(f.valor_mensalidade for f in mp_fin)

    cora_fin = FinanceiroLoja.objects.filter(provedor_boleto="cora")
    total_cora = cora_fin.count()
    ativas_cora = cora_fin.filter(status_pagamento="ativo").count()
    pendentes_cora = cora_fin.exclude(status_pagamento="ativo").count()

    return {
        "total_assinaturas": total_asaas + total_mp + total_cora,
        "assinaturas_ativas": ativas_asaas + total_mp + ativas_cora,
        "pagamentos_pendentes": pendentes_asaas_count + total_mp + pendentes_cora,
        "pagamentos_pagos": pagos_asaas_count + pagos_pl_count,
        "pagamentos_vencidos": vencidos_asaas,
        "receita_total": float(receita_asaas + receita_pl),
        "receita_pendente": float(pendente_asaas) + float(pendente_mp),
    }


_STATUS_MAP_PL = {"pago": "RECEIVED", "pendente": "PENDING", "atrasado": "OVERDUE", "cancelado": "REFUNDED"}


def _historico_assinatura_asaas(a, AsaasPayment) -> list:
    """Monta lista de histórico de pagamentos para uma LojaAssinatura (Asaas + PagamentoLoja)."""
    history = []
    seen_asaas_ids = set()
    ap_qs = AsaasPayment.objects.filter(
        models.Q(external_reference__contains=f"loja_{a.loja_slug}") | models.Q(customer=a.asaas_customer),
    ).order_by("-due_date").distinct()[:20]
    for p in ap_qs:
        seen_asaas_ids.add(p.asaas_id)
        history.append({"id": p.id, "asaas_id": p.asaas_id, "value": str(p.value), "status": p.status,
            "status_display": p.get_status_display(),
            "due_date": p.due_date.strftime("%Y-%m-%d") if p.due_date else None,
            "payment_date": p.payment_date.strftime("%Y-%m-%d") if p.payment_date else None,
            "is_paid": p.is_paid, "bank_slip_url": p.bank_slip_url or ""})
    try:
        from superadmin.models import Loja as LojaModel
        loja_obj = LojaModel.objects.filter(slug=a.loja_slug).first()
        if loja_obj:
            for pl in PagamentoLoja.objects.filter(loja=loja_obj).order_by("-data_vencimento")[:20]:
                aid = pl.asaas_payment_id or ""
                if aid and aid in seen_asaas_ids:
                    continue
                history.append({"id": pl.id, "asaas_id": aid, "value": str(pl.valor),
                    "status": _STATUS_MAP_PL.get(pl.status, "PENDING"), "status_display": pl.get_status_display(),
                    "due_date": pl.data_vencimento.strftime("%Y-%m-%d") if pl.data_vencimento else None,
                    "payment_date": pl.data_pagamento.strftime("%Y-%m-%d") if pl.data_pagamento else None,
                    "is_paid": pl.status == "pago", "bank_slip_url": pl.boleto_url or ""})
    except Exception:
        pass
    history.sort(key=lambda x: x.get("due_date") or "", reverse=True)
    return history[:20]


def _dados_loja_financeiro(loja) -> dict:
    """Identificadores usados na tabela do financeiro para trocar plano e dia."""
    try:
        financeiro = loja.financeiro
    except FinanceiroLoja.DoesNotExist:
        financeiro = None
    return {
        "loja_id": loja.id,
        "plano_id": loja.plano_id,
        "tipo_loja_id": loja.tipo_loja_id,
        "dia_vencimento": financeiro.dia_vencimento if financeiro else None,
        "tipo_assinatura": loja.tipo_assinatura,
        "financeiro_id": financeiro.id if financeiro else None,
        "bloqueada": bool(getattr(loja, "is_blocked", False)),
    }


def _id_cobranca(obj, provedor: str) -> str:
    if provedor == "cora":
        return (getattr(obj, "cora_invoice_id", None) or "").strip()
    if provedor == "mercadopago":
        return (getattr(obj, "mercadopago_payment_id", None) or "").strip()
    return (getattr(obj, "asaas_payment_id", None) or "").strip()


def _item_assinatura_provedor(f, provedor: str) -> dict:
    """Monta a assinatura de Mercado Pago ou Cora para a tabela do financeiro."""
    loja = f.loja
    data_venc = f.data_proxima_cobranca.strftime("%Y-%m-%d") if f.data_proxima_cobranca else ""
    pagamento_atual = (
        PagamentoLoja.objects.filter(loja=loja, financeiro=f, status="pendente").order_by("-data_vencimento").first()
        or PagamentoLoja.objects.filter(loja=loja, financeiro=f).order_by("-data_vencimento").first()
    )
    payment_pk = pagamento_atual.id if pagamento_atual else None
    if pagamento_atual and (pagamento_atual.pix_copy_paste or pagamento_atual.pix_qr_code):
        pix_cp, pix_qr = pagamento_atual.pix_copy_paste or "", pagamento_atual.pix_qr_code or ""
    else:
        pix_cp, pix_qr = f.pix_copy_paste or "", f.pix_qr_code or ""
    is_pago = pagamento_atual and getattr(pagamento_atual, "status", "") == "pago"
    subscription_status = "active" if f.status_pagamento == "ativo" else "inactive"
    prefixo = "cora" if provedor == "cora" else "mp"
    return {
        "id": f"{prefixo}-{f.id}",
        "loja_slug": loja.slug, "loja_nome": loja.nome,
        "plano_nome": loja.plano.nome if loja.plano else "Plano",
        "plano_valor": str(f.valor_mensalidade),
        "ativa": f.status_pagamento == "ativo",
        "subscription_status": subscription_status,
        "subscription_status_display": "Ativo" if f.status_pagamento == "ativo" else "Inativo",
        "data_vencimento": data_venc, "total_payments": 1,
        **_dados_loja_financeiro(loja),
        "current_payment_data": {
            "id": payment_pk, "asaas_id": _id_cobranca(f, provedor), "provedor": provedor,
            "customer_name": loja.nome, "value": str(f.valor_mensalidade),
            "status": "RECEIVED" if is_pago else "PENDING",
            "status_display": "Pago" if is_pago else "Pendente",
            "due_date": data_venc, "bank_slip_url": f.boleto_url or "",
            "pix_copy_paste": pix_cp, "pix_qr_code": pix_qr or None,
            "is_paid": is_pago, "is_pending": not is_pago, "is_overdue": False,
        },
        "payment_history": [
            {"id": p.id, "asaas_id": _id_cobranca(p, provedor) or p.asaas_payment_id or "",
             "provedor": provedor,
             "value": str(p.valor),
             "status": "RECEIVED" if p.status == "pago" else "PENDING" if p.status == "pendente" else "OVERDUE",
             "status_display": p.get_status_display(),
             "due_date": p.data_vencimento.strftime("%Y-%m-%d") if p.data_vencimento else None,
             "payment_date": p.data_pagamento.strftime("%Y-%m-%d") if p.data_pagamento else None,
             "is_paid": p.status == "pago", "bank_slip_url": p.boleto_url or ""}
            for p in PagamentoLoja.objects.filter(loja=loja, financeiro=f).order_by("-data_vencimento")[:20]
        ],
    }


def _preferido_da_loja(loja) -> str:
    if not loja:
        return "asaas"
    return (getattr(loja, "provedor_boleto_preferido", None) or "asaas").strip().lower()


def _marcar_banco(item: dict, loja, provedor: str) -> dict:
    """Uma loja entra na lista uma vez, no banco da assinatura."""
    pagamento = item.get("current_payment_data")
    if isinstance(pagamento, dict) and not pagamento.get("provedor"):
        pagamento["provedor"] = provedor
    item["_preferido"] = _preferido_da_loja(loja)
    return item


def _uma_assinatura_por_loja(itens: list) -> list:
    grupos: dict[str, list] = {}
    for item in itens:
        slug = item.get("loja_slug") or str(item.get("id"))
        grupos.setdefault(slug, []).append(item)
    escolhidos = []
    for grupo in grupos.values():
        preferidos = [item.get("_preferido") for item in grupo if item.get("_preferido")]
        preferido = preferidos[-1] if preferidos else "asaas"
        escolhido = next(
            (
                item for item in grupo
                if ((item.get("current_payment_data") or {}).get("provedor") or "asaas") == preferido
            ),
            grupo[0],
        )
        for item in grupo:
            item.pop("_preferido", None)
        escolhidos.append(escolhido)
    return escolhidos


def _assinaturas_unificado():
    """Uma linha por loja, no banco atual da assinatura."""
    from asaas_integration.models import AsaasPayment, LojaAssinatura
    from asaas_integration.serializers import LojaAssinaturaSerializer
    from superadmin.models import Loja as LojaModel

    out = []
    assinaturas_asaas = list(
        LojaAssinatura.objects.all().select_related("asaas_customer", "current_payment").order_by("-created_at"),
    )
    lojas_por_slug = {
        loja.slug: loja
        for loja in LojaModel.objects.filter(
            slug__in=[a.loja_slug for a in assinaturas_asaas],
        ).select_related("financeiro", "plano")
    }
    for a in assinaturas_asaas:
        data = LojaAssinaturaSerializer(a).data
        data["payment_history"] = _historico_assinatura_asaas(a, AsaasPayment)
        loja = lojas_por_slug.get(a.loja_slug)
        if loja:
            data.update(_dados_loja_financeiro(loja))
        out.append(_marcar_banco(data, loja, "asaas"))
    for f in FinanceiroLoja.objects.filter(provedor_boleto="mercadopago").exclude(mercadopago_payment_id="").select_related("loja", "loja__plano"):
        out.append(_marcar_banco(_item_assinatura_provedor(f, "mercadopago"), f.loja, "mercadopago"))
    for f in FinanceiroLoja.objects.filter(provedor_boleto="cora").select_related("loja", "loja__plano"):
        out.append(_marcar_banco(_item_assinatura_provedor(f, "cora"), f.loja, "cora"))
    return _uma_assinatura_por_loja(out)


def _pagamentos_unificado():
    """Lista unificada de pagamentos (Asaas + Mercado Pago) no formato esperado pelo frontend."""
    from asaas_integration.models import AsaasPayment
    from asaas_integration.serializers import AsaasPaymentSerializer

    out = []
    seen_asaas_ids = set()

    # 1) AsaasPayment (pagamentos registrados localmente do Asaas)
    for p in AsaasPayment.objects.all().select_related("customer").order_by("-due_date"):
        d = AsaasPaymentSerializer(p).data
        d["provedor"] = "asaas"
        out.append(d)
        if p.asaas_id:
            seen_asaas_ids.add(p.asaas_id)

    # 2) PagamentoLoja Asaas que não estão no AsaasPayment (pagamentos antigos)
    for pl in PagamentoLoja.objects.filter(
        provedor_boleto="asaas",
    ).exclude(
        asaas_payment_id="",
    ).select_related("loja", "loja__owner", "financeiro").order_by("-data_vencimento"):
        if pl.asaas_payment_id in seen_asaas_ids:
            continue
        status_map = {"pago": "RECEIVED", "pendente": "PENDING", "atrasado": "OVERDUE", "cancelado": "REFUNDED"}
        is_pago = pl.status == "pago"
        out.append({
            "id": pl.id,
            "asaas_id": pl.asaas_payment_id,
            "customer_name": pl.loja.nome,
            "customer_email": getattr(pl.loja.owner, "email", "") if pl.loja.owner else "",
            "value": str(pl.valor),
            "status": status_map.get(pl.status, "PENDING"),
            "status_display": pl.get_status_display(),
            "due_date": pl.data_vencimento.strftime("%Y-%m-%d") if pl.data_vencimento else None,
            "payment_date": pl.data_pagamento.strftime("%Y-%m-%d") if pl.data_pagamento else None,
            "bank_slip_url": pl.boleto_url or "",
            "pix_copy_paste": pl.pix_copy_paste or "",
            "is_paid": is_pago,
            "is_pending": pl.status == "pendente",
            "is_overdue": pl.status == "atrasado",
            "provedor": "asaas",
        })

    # 3) Mercado Pago
    for f in FinanceiroLoja.objects.filter(
        provedor_boleto="mercadopago",
    ).exclude(mercadopago_payment_id="").select_related("loja"):
        data_venc = f.data_proxima_cobranca.strftime("%Y-%m-%d") if f.data_proxima_cobranca else ""
        pag = (
            PagamentoLoja.objects.filter(loja=f.loja, financeiro=f)
            .order_by("-data_vencimento")
            .first()
        )
        payment_pk = pag.id if pag else f.id
        pix_cp = (pag.pix_copy_paste if pag else "") or f.pix_copy_paste or ""
        is_pago = pag and getattr(pag, "status", "") == "pago"
        payment_date_str = pag.data_pagamento.strftime("%Y-%m-%d") if pag and getattr(pag, "data_pagamento", None) else None
        out.append({
            "id": payment_pk,
            "asaas_id": f.mercadopago_payment_id,
            "customer_name": f.loja.nome,
            "customer_email": getattr(f.loja.owner, "email", ""),
            "value": str(f.valor_mensalidade),
            "status": "RECEIVED" if is_pago else "PENDING",
            "status_display": "Pago" if is_pago else "Pendente",
            "due_date": data_venc,
            "payment_date": payment_date_str,
            "bank_slip_url": f.boleto_url or "",
            "pix_copy_paste": pix_cp,
            "is_paid": is_pago,
            "is_pending": not is_pago,
            "is_overdue": False,
            "provedor": "mercadopago",
        })

    for pl in PagamentoLoja.objects.filter(provedor_boleto="cora").select_related(
        "loja", "loja__owner", "financeiro",
    ).order_by("-data_vencimento"):
        is_pago = pl.status == "pago"
        out.append({
            "id": pl.id,
            "asaas_id": (pl.cora_invoice_id or "").strip(),
            "customer_name": pl.loja.nome,
            "customer_email": getattr(pl.loja.owner, "email", "") if pl.loja.owner else "",
            "value": str(pl.valor),
            "status": _STATUS_MAP_PL.get(pl.status, "PENDING"),
            "status_display": pl.get_status_display(),
            "due_date": pl.data_vencimento.strftime("%Y-%m-%d") if pl.data_vencimento else None,
            "payment_date": pl.data_pagamento.strftime("%Y-%m-%d") if pl.data_pagamento else None,
            "bank_slip_url": pl.boleto_url or "",
            "pix_copy_paste": pl.pix_copy_paste or "",
            "is_paid": is_pago,
            "is_pending": pl.status == "pendente",
            "is_overdue": pl.status == "atrasado",
            "provedor": "cora",
        })
    return out


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def financeiro_unificado(request):
    """Resumo financeiro unificado para superadmin: Asaas + Mercado Pago.
    Retorna stats, assinaturas e pagamentos no mesmo formato dos endpoints Asaas
    para compatibilidade com a página /superadmin/financeiro.
    """
    if not request.user.is_superuser:
        return Response({"detail": "Apenas superadmin."}, status=status.HTTP_403_FORBIDDEN)
    try:
        stats = _financeiro_unificado_stats()
        assinaturas = _assinaturas_unificado()
        stats["total_assinaturas"] = len(assinaturas)
        stats["assinaturas_ativas"] = sum(1 for item in assinaturas if item.get("ativa"))
        pagamentos = _pagamentos_unificado()
        # Mesmo formato dos 3 endpoints Asaas: stats no top level + results para listas
        data = {**stats, "assinaturas": assinaturas, "pagamentos": pagamentos}
        return Response(data)
    except Exception as e:
        logger.exception("financeiro_unificado: %s", e)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
