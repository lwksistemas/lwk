"""Dashboard financeiro por loja."""
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from superadmin.services.assinatura_bloqueio_service import (
    situacao_aviso_assinatura,
    situacao_geracao_boleto_assinatura,
)

from ..loja_utils import resolve_loja_by_slug_or_atalho
from ..models import PagamentoLoja
from ..serializers import PagamentoLojaSerializer
from .helpers import (
    _boleto_pix_liberado_para_vencimento,
    _build_historico_pagamentos_loja,
    _get_or_create_financeiro_loja,
)
from .renovacao import _executar_renovar_financeiro

logger = logging.getLogger(__name__)


def _aplicar_pix_estatico_mp(financeiro, pix_copy_paste):
    """Se for MercadoPago sem PIX dinâmico, usa chave PIX estática da config como fallback."""
    if getattr(financeiro, "provedor_boleto", "") != "mercadopago":
        return pix_copy_paste
    if (pix_copy_paste or "").strip():
        return pix_copy_paste
    try:
        from .models import MercadoPagoConfig
        mp_config = MercadoPagoConfig.get_config()
        chave = (getattr(mp_config, "chave_pix_estatica", "") or "").strip()
        if chave:
            logger.info("Usando chave PIX estática como fallback para loja (MercadoPago)")
            return chave
    except Exception:
        pass
    return pix_copy_paste


def _resolver_loja_por_permissao(request, loja_slug):
    """Resolve loja conforme permissão do usuário. Retorna (loja, response_erro_ou_None)."""
    if not request.user.is_superuser:
        loja = resolve_loja_by_slug_or_atalho(loja_slug, owner=request.user, is_active=True)
        if not loja:
            return None, Response(
                {"error": "Sem permissão. Apenas o responsável pode acessar."},
                status=status.HTTP_403_FORBIDDEN,
            )
    else:
        loja = resolve_loja_by_slug_or_atalho(loja_slug, is_active=True)
        if not loja:
            return None, Response({"error": "Loja não encontrada"}, status=status.HTTP_404_NOT_FOUND)
    return loja, None


def _buscar_dados_asaas(loja, financeiro):
    """Busca boleto, PIX e estatísticas do Asaas/MercadoPago para a loja.
    Retorna (boleto_url, pix_qr_code, pix_copy_paste, proximo_boleto, stats_dict).
    stats_dict = {total, pagos, pendentes, atrasados, valor_pago, valor_pendente}
    """
    from decimal import Decimal

    boleto_url = pix_qr_code = pix_copy_paste = proximo_boleto = None
    stats = {"total": 0, "pagos": 0, "pendentes": 0, "atrasados": 0, "valor_pago": Decimal(0), "valor_pendente": Decimal(0)}

    try:
        from asaas_integration.models import AsaasPayment, LojaAssinatura
        try:
            loja_assinatura = LojaAssinatura.objects.get(loja_slug=loja.slug)
            logger.info("\u2705 LojaAssinatura encontrada: customer_id=%s", loja_assinatura.asaas_customer.asaas_id)
        except LojaAssinatura.DoesNotExist:
            pix_qr_code = financeiro.pix_qr_code or ""
            pix_copy_paste = financeiro.pix_copy_paste or ""
            if getattr(financeiro, "provedor_boleto", "") == "mercadopago" and getattr(financeiro, "mercadopago_payment_id", ""):
                try:
                    from .mercadopago_service import LojaMercadoPagoService
                    mp_svc = LojaMercadoPagoService()
                    boleto_url = mp_svc.get_boleto_url(financeiro.mercadopago_payment_id) or ""
                except Exception as mp_err:
                    logger.warning("MP get_boleto_url loja %s: %s", loja.slug, mp_err)
                    boleto_url = ""
            else:
                boleto_url = financeiro.boleto_url or ""
            logger.info("Loja %s sem LojaAssinatura (provedor=%s), usando FinanceiroLoja", loja.slug, getattr(financeiro, "provedor_boleto", "asaas"))
            return boleto_url, pix_qr_code, pix_copy_paste, None, stats

        todos_pagamentos = AsaasPayment.objects.filter(customer=loja_assinatura.asaas_customer).order_by("-due_date")
        proximo_boleto = AsaasPayment.objects.filter(
            customer=loja_assinatura.asaas_customer, status__in=["PENDING", "OVERDUE"],
        ).order_by("due_date").first()

        if proximo_boleto:
            boleto_url = proximo_boleto.bank_slip_url or proximo_boleto.invoice_url
            pix_qr_code = proximo_boleto.pix_qr_code
            pix_copy_paste = proximo_boleto.pix_copy_paste
            logger.info("\u2705 Próximo boleto: id=%s venc=%s status=%s", proximo_boleto.asaas_id, proximo_boleto.due_date, proximo_boleto.status)
        else:
            logger.warning("\u26a0\ufe0f Nenhum boleto pendente para %s", loja.nome)

        stats["total"] = todos_pagamentos.count()
        stats["pagos"] = todos_pagamentos.filter(status__in=["RECEIVED", "CONFIRMED", "RECEIVED_IN_CASH"]).count()
        stats["pendentes"] = todos_pagamentos.filter(status="PENDING").count()
        stats["atrasados"] = todos_pagamentos.filter(status="OVERDUE").count()
        for pag in todos_pagamentos.filter(status__in=["RECEIVED", "CONFIRMED", "RECEIVED_IN_CASH"]):
            stats["valor_pago"] += Decimal(str(pag.value))
        for pag in todos_pagamentos.filter(status__in=["PENDING", "OVERDUE"]):
            stats["valor_pendente"] += Decimal(str(pag.value))

    except Exception as e:
        logger.error("\u274c Erro ao buscar boleto Asaas loja %s: %s", loja.nome, e)
        boleto_url = financeiro.boleto_url
        pix_qr_code = financeiro.pix_qr_code
        pix_copy_paste = financeiro.pix_copy_paste

    return boleto_url, pix_qr_code, pix_copy_paste, proximo_boleto, stats


def _merge_estatisticas_pagamento(stats_asaas, pagamentos_loja_qs):
    """Preferência de estatísticas: Asaas se houver registros, senão PagamentoLoja."""
    total_asaas = stats_asaas["total"]
    if total_asaas > 0:
        return {
            "total": total_asaas,
            "pagos": stats_asaas["pagos"],
            "pendentes": stats_asaas["pendentes"],
            "atrasados": stats_asaas["atrasados"],
            "valor_pago": float(stats_asaas["valor_pago"]),
            "valor_pendente": float(stats_asaas["valor_pendente"]),
        }
    return {
        "total": pagamentos_loja_qs.count(),
        "pagos": pagamentos_loja_qs.filter(status="pago").count(),
        "pendentes": pagamentos_loja_qs.filter(status="pendente").count(),
        "atrasados": pagamentos_loja_qs.filter(status="atrasado").count(),
        "valor_pago": sum(p.valor for p in pagamentos_loja_qs.filter(status="pago")),
        "valor_pendente": sum(p.valor for p in pagamentos_loja_qs.filter(status__in=["pendente", "atrasado"])),
    }


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def dashboard_financeiro_loja(request, loja_slug):
    """Dashboard financeiro específico de uma loja (GET). POST gera cobrança antecipada."""
    if request.method == "POST":
        logger.info("POST financeiro/ (gerar cobrança) loja_slug=%s user=%s", loja_slug, request.user.username)
        if not request.user.is_superuser:
            loja = resolve_loja_by_slug_or_atalho(loja_slug, owner=request.user, is_active=True)
            if not loja:
                return Response(
                    {"success": False, "error": "Sem permissão. Apenas o responsável pode gerar cobrança."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        else:
            loja = resolve_loja_by_slug_or_atalho(loja_slug, is_active=True)
            if not loja:
                return Response(
                    {"success": False, "error": "Loja não encontrada"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        try:
            financeiro = _get_or_create_financeiro_loja(loja)
        except Exception as e:
            logger.exception("dashboard_financeiro_loja POST %s: %s", loja_slug, e)
            return Response(
                {"success": False, "error": "Não foi possível carregar o financeiro da loja."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return _executar_renovar_financeiro(financeiro, request.data)

    try:
        return _dashboard_financeiro_loja_impl(request, loja_slug)
    except Exception as e:
        logger.exception("dashboard_financeiro_loja %s: %s", loja_slug, e)
        return Response(
            {"error": "Erro ao carregar dados financeiros. Tente novamente em instantes."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
def _dashboard_financeiro_loja_impl(request, loja_slug):
    loja, err = _resolver_loja_por_permissao(request, loja_slug)
    if err:
        return err

    try:
        financeiro = _get_or_create_financeiro_loja(loja)
    except Exception as e:
        logger.exception("Erro ao obter/criar financeiro loja %s: %s", loja_slug, e)
        return Response(
            {"error": "Não foi possível carregar o financeiro desta loja. Tente novamente ou contate o suporte."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    pagamentos = PagamentoLoja.objects.filter(loja=loja).exclude(status="cancelado").order_by("-data_vencimento")
    proximo_pagamento = pagamentos.filter(status="pendente").first()

    logger.info("🔍 Buscando boleto para loja: %s (slug: %s)", loja.nome, loja.slug)
    boleto_url, pix_qr_code, pix_copy_paste, proximo_boleto, stats_asaas = _buscar_dados_asaas(loja, financeiro)
    est = _merge_estatisticas_pagamento(stats_asaas, pagamentos)

    try:
        historico_pagamentos = _build_historico_pagamentos_loja(
            loja,
            financeiro,
            boleto_url or "",
            pix_copy_paste or "",
            proximo_boleto.due_date if proximo_boleto else None,
        )
        logger.info(f"✅ Histórico loja {loja.slug}: {len(historico_pagamentos)} itens")
    except Exception as e:
        logger.exception("Erro ao montar histórico de pagamentos loja %s: %s", loja.slug, e)
        historico_pagamentos = []

    pix_copy_paste = _aplicar_pix_estatico_mp(financeiro, pix_copy_paste)

    vencimento_boleto = (
        proximo_boleto.due_date
        if proximo_boleto and proximo_boleto.due_date
        else financeiro.data_proxima_cobranca
    )
    if vencimento_boleto and not _boleto_pix_liberado_para_vencimento(vencimento_boleto):
        boleto_url = None
        pix_qr_code = None
        pix_copy_paste = None

    return Response({
        "loja": {
            "id": loja.id,
            "nome": loja.nome,
            "slug": loja.slug,
            "plano": loja.plano.nome,
            "tipo_assinatura": loja.get_tipo_assinatura_display(),
        },
        "financeiro": {
            "id": financeiro.id,
            "status_pagamento": financeiro.get_status_pagamento_display(),
            "valor_mensalidade": float(financeiro.valor_mensalidade),
            "data_proxima_cobranca": financeiro.data_proxima_cobranca.strftime("%Y-%m-%d") if financeiro.data_proxima_cobranca else None,
            "ultimo_pagamento": financeiro.ultimo_pagamento.strftime("%Y-%m-%d") if financeiro.ultimo_pagamento else None,
            "dia_vencimento": financeiro.dia_vencimento,
            "total_pago": float(financeiro.total_pago),
            "total_pendente": float(financeiro.total_pendente),
            "tem_asaas": bool(financeiro.asaas_payment_id) or bool(boleto_url),
            "tem_mercadopago": bool(getattr(financeiro, "mercadopago_payment_id", None)) or getattr(financeiro, "provedor_boleto", "asaas") == "mercadopago",
            "provedor_boleto": getattr(financeiro, "provedor_boleto", "asaas"),
            "asaas_customer_id": financeiro.asaas_customer_id,
            "asaas_payment_id": financeiro.asaas_payment_id,
            "boleto_url": boleto_url,
            "pix_qr_code": pix_qr_code,
            "pix_copy_paste": pix_copy_paste,
        },
        "estatisticas": {
            "total_pagamentos": est["total"],
            "pagamentos_pagos": est["pagos"],
            "pagamentos_pendentes": est["pendentes"],
            "pagamentos_atrasados": est["atrasados"],
            "valor_total_pago": float(est["valor_pago"]),
            "valor_total_pendente": float(est["valor_pendente"]),
            "taxa_pagamento": (est["pagos"] / est["total"] * 100) if est["total"] > 0 else 0,
        },
        "proximo_pagamento": PagamentoLojaSerializer(proximo_pagamento).data if proximo_pagamento else None,
        "pagamentos_recentes": PagamentoLojaSerializer(pagamentos[:5], many=True).data,
        "historico_pagamentos": historico_pagamentos,
        "assinatura_aviso": situacao_aviso_assinatura(loja),
        "is_blocked": bool(getattr(loja, "is_blocked", False)),
        "geracao_boleto": situacao_geracao_boleto_assinatura(loja, financeiro),
    })
