"""Helpers de formatação e contexto do recibo de pagamento."""
import logging
import re
from decimal import Decimal, InvalidOperation

from core.cpf_utils import eh_cnpj, eh_cpf, normalizar_cpf_cnpj
from core.phone_utils import telefone_exibicao_brasileiro

logger = logging.getLogger(__name__)


def _formatar_data_recibo(dt) -> str:
    """Formata data/hora do recibo no fuso America/Sao_Paulo (evita UTC no PDF)."""
    if not dt:
        return "—"
    from django.utils import timezone as dj_tz

    if dj_tz.is_aware(dt):
        dt = dj_tz.localtime(dt)
    return dt.strftime("%d/%m/%Y %H:%M")


def _label_documento_loja(cpf_cnpj: str) -> str:
    """Rótulo CPF ou CNPJ conforme quantidade de dígitos."""
    if eh_cpf(cpf_cnpj):
        return "CPF"
    if eh_cnpj(cpf_cnpj):
        return "CNPJ"
    return "CPF/CNPJ"


def _extrair_desconto_notes(payment) -> float:
    """Lê desconto gravado em payment.notes (ex.: 'Desconto: R$ 200.00')."""
    notes = (getattr(payment, "notes", None) or "").strip()
    if not notes:
        return 0.0
    m = re.search(r"Desconto:\s*R\$\s*([\d.,]+)", notes, re.IGNORECASE)
    if not m:
        return 0.0
    raw = m.group(1).strip()
    if "," in raw and "." in raw:
        # 1.200,50
        raw = raw.replace(".", "").replace(",", ".")
    elif "," in raw:
        raw = raw.replace(",", ".")
    try:
        return float(Decimal(raw))
    except (InvalidOperation, ValueError):
        return 0.0


def _obter_dados_contexto(payment, patient, appointment) -> dict:
    """Obtém dados completos para o recibo."""
    from superadmin.models import Loja

    loja = Loja.objects.filter(id=payment.loja_id).first()
    professional = getattr(appointment, "professional", None)

    procs = []
    try:
        ap_procs = appointment.appointment_procedures.select_related("procedure").all()
        for ap in ap_procs:
            procs.append({"nome": ap.procedure.nome, "valor": float(ap.get_valor())})
    except Exception:
        logger.exception("Erro ao listar procedimentos do recibo (payment %s)", payment.id)
    if not procs and appointment.procedure:
        procs = [{"nome": appointment.procedure.nome, "valor": float(appointment.procedure.preco or 0)}]

    taxa_consulta = 0.0
    taxa_consulta_referencia = 0.0
    retorno_gratuito = False
    retorno_dias = None
    retorno_aviso = ""
    try:
        consulta = getattr(appointment, "consulta", None)
        if consulta:
            taxa_consulta = float(getattr(consulta, "valor_consulta", 0) or 0)
        from .retorno_info import montar_info_retorno_recibo

        info_ret = montar_info_retorno_recibo(
            consulta, appointment, loja_id=payment.loja_id,
        )
        retorno_gratuito = bool(info_ret.get("retorno_gratuito"))
        taxa_consulta_referencia = float(info_ret.get("taxa_consulta_referencia") or 0)
        retorno_dias = info_ret.get("retorno_dias")
        retorno_aviso = (info_ret.get("retorno_aviso") or "").strip()
        if retorno_gratuito and taxa_consulta_referencia <= 0 and taxa_consulta > 0:
            taxa_consulta_referencia = taxa_consulta
    except Exception:
        logger.exception("Erro ao ler taxa de consulta do recibo (payment %s)", payment.id)

    doc_raw = (getattr(loja, "cpf_cnpj", "") or "") if loja else ""
    tel_raw = (getattr(loja, "owner_telefone", "") or "") if loja else ""
    cep_raw = (getattr(loja, "cep", "") or "") if loja else ""
    desconto = _extrair_desconto_notes(payment)
    valor_total = float(payment.valor_total_efetivo)
    valor_pago = float(payment.amount or 0)
    desconto_retorno = (
        float(taxa_consulta_referencia)
        if retorno_gratuito and taxa_consulta_referencia > 0
        else 0.0
    )
    taxa_para_subtotal = (
        taxa_consulta_referencia if retorno_gratuito and taxa_consulta_referencia > 0 else taxa_consulta
    )
    servicos_soma = taxa_para_subtotal + sum(p["valor"] for p in procs)
    if desconto_retorno > 0 or desconto > 0:
        subtotal = servicos_soma
    else:
        subtotal = servicos_soma if servicos_soma > 0 else valor_total
    loja_telefone = telefone_exibicao_brasileiro(tel_raw)
    loja_cep = _formatar_cep(cep_raw)
    loja_email = (getattr(getattr(loja, "owner", None), "email", "") or "").strip() if loja else ""

    return {
        "paciente_nome": getattr(patient, "nome", "Cliente"),
        "paciente_email": (getattr(patient, "email", "") or "").strip(),
        "paciente_telefone": telefone_exibicao_brasileiro(getattr(patient, "telefone", "") or ""),
        "profissional_nome": getattr(professional, "nome", "") if professional else "",
        "loja_nome": getattr(loja, "nome", "") if loja else "",
        "loja_documento": normalizar_cpf_cnpj(doc_raw),
        "loja_documento_label": _label_documento_loja(doc_raw),
        "loja_cnpj": normalizar_cpf_cnpj(doc_raw),  # compat
        "loja_endereco": _formatar_endereco_loja(loja) if loja else "",
        "loja_telefone": loja_telefone,
        "loja_cep": loja_cep,
        "loja_email": loja_email,
        "loja_tel_cep": _linha_tel_cep(loja_telefone, loja_cep),
        "procedimentos": procs,
        "taxa_consulta": taxa_consulta,
        "taxa_consulta_referencia": taxa_consulta_referencia,
        "retorno_gratuito": retorno_gratuito,
        "retorno_dias": retorno_dias,
        "retorno_aviso": retorno_aviso,
        "subtotal": float(subtotal),
        "desconto": desconto,
        "desconto_retorno": desconto_retorno,
        "valor_total": valor_total,
        "valor_pago": valor_pago,
        "metodo": (
            payment.get_payment_method_display()
            if hasattr(payment, "get_payment_method_display")
            else payment.payment_method
        ),
        "formas_pagamento": _listar_formas_pagamento(payment),
        "data": _formatar_data_recibo(payment.payment_date),
        "data_atendimento": _formatar_data_recibo(getattr(appointment, "date", None)),
    }


def _formas_pagamento_texto(ctx: dict) -> str:
    """Formata formas de pagamento para texto (WhatsApp/email)."""
    formas = ctx.get("formas_pagamento", [])
    if not formas:
        metodo = ctx.get("metodo", "")
        return f'  {metodo} — R$ {ctx.get("valor_pago", 0):.2f}\n'
    lines = [f'  • {f["metodo"]} — R$ {f["valor"]:.2f}' for f in formas]
    return "\n".join(lines) + "\n"


def _formas_pagamento_html(ctx: dict) -> str:
    """Formata formas de pagamento para HTML (corpo do email)."""
    formas = ctx.get("formas_pagamento", [])
    if not formas:
        metodo = ctx.get("metodo", "")
        return f'<li>{metodo} — R$ {ctx.get("valor_pago", 0):.2f}</li>'
    return "".join(
        f'<li>{f["metodo"]} — R$ {f["valor"]:.2f}</li>' for f in formas
    )


def _listar_formas_pagamento(payment) -> list[dict]:
    """Retorna lista de formas de pagamento usadas (com valor cada)."""
    METODOS = dict(payment.PAYMENT_METHOD_CHOICES)
    try:
        parcelas = payment.parcelas.filter(status="PAID").order_by("payment_date")
        if parcelas.exists():
            return [
                {"metodo": METODOS.get(p.payment_method, p.payment_method), "valor": float(p.valor)}
                for p in parcelas
            ]
    except Exception:
        logger.exception("Erro ao listar parcelas do recibo (payment %s)", payment.id)
    metodo_label = METODOS.get(payment.payment_method, payment.payment_method)
    return [{"metodo": metodo_label, "valor": float(payment.amount or 0)}]


def _formatar_cep(cep: str) -> str:
    """Formata CEP no padrão XXXXX-XXX."""
    if not cep:
        return ""
    d = re.sub(r"\D", "", str(cep))
    if len(d) == 8:
        return f"{d[:5]}-{d[5:]}"
    return str(cep).strip()


def _formatar_endereco_loja(loja, *, incluir_cep: bool = False) -> str:
    """Monta endereço da loja (sem CEP por padrão — CEP vai com o telefone)."""
    partes = []
    if getattr(loja, "logradouro", ""):
        end = loja.logradouro
        if getattr(loja, "numero", ""):
            end += f", {loja.numero}"
        partes.append(end)
    if getattr(loja, "bairro", ""):
        partes.append(loja.bairro)
    if getattr(loja, "cidade", ""):
        cidade = loja.cidade
        if getattr(loja, "uf", ""):
            cidade += f" - {loja.uf}"
        partes.append(cidade)
    if incluir_cep and getattr(loja, "cep", ""):
        partes.append(f"CEP {_formatar_cep(loja.cep)}")
    return ", ".join(partes)


def _linha_tel_cep(telefone: str = "", cep: str = "") -> str:
    """Telefone e CEP na mesma linha do cabeçalho do recibo."""
    partes = []
    if telefone:
        partes.append(f"Tel: {telefone}")
    if cep:
        partes.append(f"CEP {cep}")
    return "  ·  ".join(partes)


def _linha_documento_loja(ctx: dict) -> str:
    doc = ctx.get("loja_documento") or ctx.get("loja_cnpj") or ""
    if not doc:
        return ""
    label = ctx.get("loja_documento_label") or _label_documento_loja(doc)
    return f"{label}: {doc}"


def _linhas_taxa_consulta_recibo(ctx: dict) -> list[tuple[str, float]]:
    """Linha da taxa de consulta no recibo (valor de tabela quando há retorno)."""
    if ctx.get("retorno_gratuito"):
        ref = float(ctx.get("taxa_consulta_referencia") or 0)
        if ref > 0:
            return [("Taxa de consulta", ref)]
        return []
    taxa = float(ctx.get("taxa_consulta") or 0)
    if taxa > 0:
        return [("Taxa de consulta", taxa)]
    return []


def _label_desconto_retorno_recibo(ctx: dict) -> str:
    dias = ctx.get("retorno_dias")
    if dias:
        return f"Desconto retorno (prazo {int(dias)} dias)"
    return "Desconto retorno"


def _linhas_descontos_recibo(ctx: dict) -> list[tuple[str, float]]:
    """Linhas de desconto (retorno gratuito e desconto comercial)."""
    linhas: list[tuple[str, float]] = []
    desconto_retorno = float(ctx.get("desconto_retorno") or 0)
    if desconto_retorno <= 0 and ctx.get("retorno_gratuito"):
        desconto_retorno = float(ctx.get("taxa_consulta_referencia") or 0)
    if desconto_retorno > 0:
        linhas.append((_label_desconto_retorno_recibo(ctx), desconto_retorno))
    desconto = float(ctx.get("desconto") or 0)
    if desconto > 0:
        linhas.append(("Desconto", desconto))
    return linhas