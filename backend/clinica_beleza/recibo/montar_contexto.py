"""Monta o dicionário que o HTML e o PDF leem."""
import logging

from core.cpf_utils import normalizar_cpf_cnpj
from core.phone_utils import telefone_exibicao_brasileiro

from .desconto_recibo import desconto_concedido
from .itens_recibo import (
    _buscar_procedimentos_recibo,
    _calcular_subtotal_recibo,
    _calcular_taxa_retorno_recibo,
    _local_convenio_recibo,
    aplicar_valor_consulta_do_local,
)
from .loja_recibo import _dados_loja_recibo
from .pagamento_recibo import _listar_formas_pagamento
from .protocolo_recibo import _dados_protocolo_recibo
from .quando_recibo import _agora_recibo, _formatar_data_recibo

logger = logging.getLogger(__name__)


def _nome_de_quem_recebeu(payment) -> str:
    from clinica_beleza.venda_produto_service import nome_operador_pagamento

    return nome_operador_pagamento(payment)


def _dados_assinatura_recibo(payment) -> dict | None:
    """Se o recibo já foi assinado pelo cliente, retorna os dados da assinatura
    (para o PDF exibir a seção de assinatura em qualquer canal: email/WhatsApp/download).
    """
    try:
        from clinica_beleza.models import ReciboAssinatura

        ass = (
            ReciboAssinatura.objects.filter(payment=payment, tipo="paciente", assinado=True)
            .order_by("assinado_em")
            .first()
        )
        if not ass:
            return None
        assinado_em = ass.assinado_em
        if assinado_em is not None and hasattr(assinado_em, "strftime"):
            from django.utils import timezone as dj_tz

            if dj_tz.is_aware(assinado_em):
                assinado_em = dj_tz.localtime(assinado_em)
            assinado_em = assinado_em.strftime("%d/%m/%Y %H:%M")
        return {
            "nome": ass.nome_assinante,
            "cpf": normalizar_cpf_cnpj(
                (getattr(payment.appointment.patient, "cpf", "") or "") if payment.appointment else "",
            ),
            "email": (ass.email_assinante or "").strip(),
            "ip": ass.ip_address,
            "assinado_em": assinado_em or "",
        }
    except Exception:
        logger.exception("Erro ao ler assinatura do recibo (payment %s)", getattr(payment, "id", None))
        return None


def _obter_dados_contexto(payment, patient, appointment) -> dict:
    """Obtém dados completos para o recibo."""
    from superadmin.models import Loja

    loja = Loja.objects.filter(id=payment.loja_id).first()
    professional = getattr(appointment, "professional", None) if appointment is not None else None
    from clinica_beleza.venda_produto_service import produtos_do_pagamento

    produtos = produtos_do_pagamento(payment)
    somente_produtos = appointment is None
    procs = [] if somente_produtos else _buscar_procedimentos_recibo(appointment)

    taxa_info = (
        {
            "taxa_consulta": 0.0,
            "taxa_consulta_referencia": 0.0,
            "retorno_gratuito": False,
            "retorno_dias": None,
            "retorno_aviso": "",
            "cobrar_taxa_com_procedimento": True,
        }
        if somente_produtos
        else _calcular_taxa_retorno_recibo(appointment, payment.loja_id)
    )
    desconto = desconto_concedido(payment)
    valor_total = float(payment.valor_total_efetivo)
    # Valor pago = só o que foi efetivamente recebido (parcelas). "A prazo" não é pago.
    try:
        valor_pago = float(payment.valor_pago_parcelas)
    except Exception:
        valor_pago = float(payment.amount or 0)
    try:
        saldo_devedor = float(payment.saldo_devedor)
    except Exception:
        saldo_devedor = max(valor_total - valor_pago, 0.0)
    venc = getattr(payment, "data_vencimento", None)
    vencimento = venc.strftime("%d/%m/%Y") if venc else ""
    subtotal, desconto_retorno = _calcular_subtotal_recibo(taxa_info, procs, valor_total, desconto)

    ctx = aplicar_valor_consulta_do_local({
        **taxa_info,
        "procedimentos": procs,
        "subtotal": float(subtotal),
        "valor_total": valor_total,
        "valor_pago": valor_pago,
        "saldo_devedor": saldo_devedor,
    })
    subtotal = float(ctx["subtotal"])
    valor_total = float(ctx["valor_total"])
    saldo_devedor = float(ctx["saldo_devedor"])
    taxa_info = {
        "taxa_consulta": ctx["taxa_consulta"],
        "taxa_consulta_referencia": ctx["taxa_consulta_referencia"],
        "retorno_gratuito": ctx["retorno_gratuito"],
        "retorno_dias": ctx["retorno_dias"],
        "retorno_aviso": ctx["retorno_aviso"],
        "cobrar_taxa_com_procedimento": ctx.get("cobrar_taxa_com_procedimento", True),
    }

    ctx = _dados_loja_recibo(loja)
    assinatura_recibo = _dados_assinatura_recibo(payment)
    protocolo_recibo = {} if somente_produtos else _dados_protocolo_recibo(appointment)

    return {
        **ctx,
        "assinatura_recibo": assinatura_recibo,
        "paciente_nome": (getattr(patient, "nome", "") or "").strip() or (
            "Consumidor não identificado" if somente_produtos else "Cliente"
        ),
        "paciente_cpf": normalizar_cpf_cnpj(getattr(patient, "cpf", "") or ""),
        "paciente_email": (getattr(patient, "email", "") or "").strip(),
        "paciente_telefone": telefone_exibicao_brasileiro(getattr(patient, "telefone", "") or ""),
        "profissional_nome": getattr(professional, "nome", "") if professional else "",
        "operador_nome": _nome_de_quem_recebeu(payment),
        "caixa_nome": (getattr(getattr(getattr(payment, "venda_balcao", None), "sessao", None), "nome", "") or "").strip(),
        "procedimentos": procs,
        "produtos": produtos,
        "somente_produtos": somente_produtos,
        **({} if somente_produtos else _local_convenio_recibo(appointment)),
        "subtotal": float(subtotal),
        "desconto": desconto,
        "desconto_retorno": desconto_retorno,
        "valor_total": valor_total,
        "valor_pago": valor_pago,
        "saldo_devedor": saldo_devedor,
        "vencimento": vencimento,
        "metodo": (
            payment.get_payment_method_display()
            if hasattr(payment, "get_payment_method_display")
            else payment.payment_method
        ),
        "formas_pagamento": _listar_formas_pagamento(payment),
        "condicao_cobranca": (
            "a prazo" if getattr(payment, "payment_method", "") == "PRAZO" else ""
        ),
        "data": _formatar_data_recibo(payment.payment_date),
        "data_emissao": _formatar_data_recibo(_agora_recibo()),
        "data_atendimento": _formatar_data_recibo(
            getattr(appointment, "date", None) if appointment is not None else getattr(payment, "payment_date", None)
        ),
        "recibo_numero": getattr(payment, "id", None),
        **taxa_info,
        **protocolo_recibo,
    }
