"""Helpers de formatação e contexto do recibo de pagamento."""
import logging
import re
from decimal import Decimal, InvalidOperation

from core.cpf_utils import eh_cnpj, eh_cpf, normalizar_cpf_cnpj
from core.phone_utils import telefone_exibicao_brasileiro

from .moeda import formatar_moeda_recibo

logger = logging.getLogger(__name__)


def _agora_recibo():
    """Momento atual (aware) para a data de emissão do recibo."""
    from django.utils import timezone as dj_tz

    return dj_tz.now()


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


def desconto_concedido(payment) -> float:
    """Desconto comercial do atendimento: campo Payment.desconto, senão notes."""
    try:
        campo = float(getattr(payment, "desconto", 0) or 0)
    except (TypeError, ValueError):
        campo = 0.0
    if campo > 0:
        return campo
    return _extrair_desconto_notes(payment)


def _buscar_procedimentos_recibo(appointment) -> list[dict]:
    procs = []
    try:
        ap_procs = appointment.appointment_procedures.select_related("procedure").all()
        for ap in ap_procs:
            procs.append({
                "nome": ap.procedure.nome,
                "valor": float(ap.get_valor()),
                "preco_cadastro": float(getattr(ap.procedure, "preco", 0) or 0),
            })
    except Exception:
        logger.exception("Erro ao listar procedimentos do recibo")
    if not procs and appointment.procedure:
        nome_legado = getattr(appointment.procedure, "nome", "") or ""
        if isinstance(nome_legado, str) and nome_legado.strip() and nome_legado.strip().casefold() != "consulta":
            procs = [{"nome": nome_legado.strip(), "valor": float(appointment.procedure.preco or 0)}]
    procs = _anexar_procedimento_do_retorno(appointment, procs)
    if not procs:
        procs.append({"nome": "Consulta", "valor": 0.0})
    return procs


def _anexar_procedimento_do_retorno(appointment, procs: list[dict]) -> list[dict]:
    """Retorno sem valor ainda precisa citar o procedimento realizado."""
    nomes = {
        (p.get("nome") or "").strip().casefold()
        for p in procs
        if isinstance(p.get("nome"), str)
    }
    retorno = getattr(appointment, "retorno_procedure", None)
    nome_retorno = getattr(retorno, "nome", None)
    if isinstance(nome_retorno, str) and nome_retorno.strip() and nome_retorno.strip().casefold() not in nomes:
        procs.append({"nome": nome_retorno.strip(), "valor": 0.0})
        return procs
    if procs:
        return procs
    consulta = getattr(appointment, "consulta", None)
    if consulta is None or not getattr(consulta, "pk", None):
        return procs
    try:
        from django.db.models import Model

        if not isinstance(consulta, Model):
            return procs
        evo = consulta.evolucoes.order_by("-created_at").first()
    except Exception:
        logger.exception("Erro ao ler procedimento realizado do retorno")
        return procs
    texto = getattr(evo, "procedimento_realizado", "") if evo else ""
    if isinstance(texto, str) and texto.strip():
        procs.append({"nome": texto.strip(), "valor": 0.0})
    return procs


def _calcular_taxa_retorno_recibo(appointment, loja_id):
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

        info_ret = montar_info_retorno_recibo(consulta, appointment, loja_id=loja_id)
        retorno_gratuito = bool(info_ret.get("retorno_gratuito"))
        taxa_consulta_referencia = float(info_ret.get("taxa_consulta_referencia") or 0)
        retorno_dias = info_ret.get("retorno_dias")
        retorno_aviso = (info_ret.get("retorno_aviso") or "").strip()
        if retorno_gratuito and taxa_consulta_referencia <= 0 and taxa_consulta > 0:
            taxa_consulta_referencia = taxa_consulta
    except Exception:
        logger.exception("Erro ao ler taxa de consulta do recibo")
    return {
        "taxa_consulta": taxa_consulta,
        "taxa_consulta_referencia": taxa_consulta_referencia,
        "retorno_gratuito": retorno_gratuito,
        "retorno_dias": retorno_dias,
        "retorno_aviso": retorno_aviso,
    }


def _calcular_subtotal_recibo(taxa_info, procs, valor_total, desconto):
    taxa_consulta = taxa_info["taxa_consulta"]
    taxa_consulta_referencia = taxa_info["taxa_consulta_referencia"]
    retorno_gratuito = taxa_info["retorno_gratuito"]
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
    return subtotal, desconto_retorno


def _dados_loja_recibo(loja):
    from superadmin.loja_utils import contato_publico_loja

    doc_raw = (getattr(loja, "cpf_cnpj", "") or "") if loja else ""
    cep_raw = (getattr(loja, "cep", "") or "") if loja else ""
    tel_raw, email_raw = contato_publico_loja(loja)
    loja_telefone = telefone_exibicao_brasileiro(tel_raw)
    loja_cep = _formatar_cep(cep_raw)
    logo_url = ""
    if loja:
        logo_url = (getattr(loja, "logo", "") or "").strip() or (getattr(loja, "login_logo", "") or "").strip()
    return {
        "loja_nome": getattr(loja, "nome", "") if loja else "",
        "loja_documento": normalizar_cpf_cnpj(doc_raw),
        "loja_documento_label": _label_documento_loja(doc_raw),
        "loja_cnpj": normalizar_cpf_cnpj(doc_raw),
        "loja_endereco": _formatar_endereco_loja(loja) if loja else "",
        "loja_telefone": loja_telefone,
        "loja_cep": loja_cep,
        "loja_email": email_raw,
        "loja_tel_cep": _linha_tel_cep(loja_telefone, loja_cep),
        "logo_url": logo_url,
    }


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
    professional = getattr(appointment, "professional", None)
    procs = _buscar_procedimentos_recibo(appointment)

    taxa_info = _calcular_taxa_retorno_recibo(appointment, payment.loja_id)
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
    }

    ctx = _dados_loja_recibo(loja)
    assinatura_recibo = _dados_assinatura_recibo(payment)

    return {
        **ctx,
        "assinatura_recibo": assinatura_recibo,
        "paciente_nome": getattr(patient, "nome", "Cliente"),
        "paciente_cpf": normalizar_cpf_cnpj(getattr(patient, "cpf", "") or ""),
        "paciente_email": (getattr(patient, "email", "") or "").strip(),
        "paciente_telefone": telefone_exibicao_brasileiro(getattr(patient, "telefone", "") or ""),
        "profissional_nome": getattr(professional, "nome", "") if professional else "",
        "procedimentos": procs,
        **_local_convenio_recibo(appointment),
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
        "data_atendimento": _formatar_data_recibo(getattr(appointment, "date", None)),
        "recibo_numero": getattr(payment, "id", None),
        **taxa_info,
    }


def _formas_pagamento_texto(ctx: dict) -> str:
    """Formata formas de pagamento para texto (WhatsApp/email)."""
    formas = ctx.get("formas_pagamento", [])
    if not formas:
        if float(ctx.get("valor_pago") or 0) <= 0.009:
            condicao = (ctx.get("condicao_cobranca") or "").strip()
            if condicao:
                return f"  Condição de cobrança: {condicao}\n"
            return ""
        metodo = ctx.get("metodo", "")
        return f"  {metodo} — {formatar_moeda_recibo(ctx.get('valor_pago', 0))}\n"
    lines = [f'  • {f["metodo"]} — {formatar_moeda_recibo(f["valor"])}' for f in formas]
    return "\n".join(lines) + "\n"


def _formas_pagamento_html(ctx: dict) -> str:
    """Formata formas de pagamento para HTML (corpo do email)."""
    formas = ctx.get("formas_pagamento", [])
    if not formas:
        metodo = ctx.get("metodo", "")
        return f"<li>{metodo} — {formatar_moeda_recibo(ctx.get('valor_pago', 0))}</li>"
    return "".join(
        f'<li>{f["metodo"]} — {formatar_moeda_recibo(f["valor"])}</li>' for f in formas
    )


def _listar_formas_pagamento(payment) -> list[dict]:
    """Retorna formas de pagamento do recibo.

    Agrupa por forma + data do pagamento (mesma forma no mesmo dia soma numa linha).
    Sempre exibe a data em que o cliente pagou cada forma — não confundir com a data
    de emissão do recibo.
    """
    from collections import OrderedDict

    METODOS = dict(payment.PAYMENT_METHOD_CHOICES)
    try:
        parcelas = list(
            payment.parcelas.filter(status="PAID").order_by("payment_date", "id"),
        )
        if parcelas:
            grupos: OrderedDict[tuple[str, str], dict] = OrderedDict()
            for p in parcelas:
                data = getattr(p, "payment_date", None)
                data_key = data.isoformat() if hasattr(data, "isoformat") else str(data or "")
                key = (str(p.payment_method or ""), data_key)
                if key not in grupos:
                    grupos[key] = {
                        "metodo_code": p.payment_method,
                        "data": data,
                        "valor": 0.0,
                    }
                grupos[key]["valor"] += float(p.valor or 0)

            datas = {g["data"] for g in grupos.values() if g["data"]}
            del datas  # mantido por compatibilidade histórica
            result = []
            for g in grupos.values():
                label = METODOS.get(g["metodo_code"], g["metodo_code"])
                # Sempre mostra a data do pagamento (não confundir com a emissão do recibo).
                if g["data"] is not None and hasattr(g["data"], "strftime"):
                    label = f"{label} ({g['data'].strftime('%d/%m/%Y')})"
                valor = round(g["valor"], 2)
                if valor <= 0.009:
                    continue
                result.append({"metodo": label, "valor": valor})
            return result
    except Exception:
        logger.exception("Erro ao listar parcelas do recibo (payment %s)", payment.id)
    # A prazo, ou método gravado com valor zero, não é forma de pagamento.
    if payment.payment_method == "PRAZO" or float(payment.amount or 0) <= 0.009:
        return []
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


def recibo_so_consulta(ctx: dict) -> bool:
    """Atendimento sem procedimento cobrado: o recibo precisa citar a consulta."""
    for p in ctx.get("procedimentos") or []:
        if float(p.get("valor") or 0) > 0.009:
            return False
        nome = (p.get("nome") or "").strip().casefold()
        if nome and nome not in ("consulta", "taxa de consulta"):
            return False
    return True


def _nome_cadastro(obj) -> str:
    nome = getattr(obj, "nome", "") if obj is not None else ""
    return nome.strip() if isinstance(nome, str) else ""


def _local_convenio_recibo(appointment) -> dict:
    consulta = getattr(appointment, "consulta", None)
    local = getattr(consulta, "local_atendimento", None) if consulta is not None else None
    if local is None:
        local = getattr(appointment, "local_atendimento", None)
    convenio = getattr(consulta, "convenio", None) if consulta is not None else None
    if convenio is None:
        convenio = getattr(appointment, "convenio", None)
    return {
        "local_nome": _nome_cadastro(local),
        "convenio_nome": _nome_cadastro(convenio) or "Particular",
    }


def linhas_local_convenio_recibo(ctx: dict) -> list[tuple[str, str]]:
    """Convênio só no recibo de consulta, sem outro procedimento. O local não entra no cupom."""
    if not recibo_so_consulta(ctx):
        return []
    convenio = (ctx.get("convenio_nome") or "").strip()
    if isinstance(convenio, str) and convenio:
        return [("Convênio", convenio)]
    return []


def aplicar_valor_consulta_do_local(ctx: dict) -> dict:
    """Usa a taxa do local quando a consulta ficou zerada (com ou sem procedimento).

    Fora do retorno gratuito a taxa entra no recibo sempre; no retorno a linha
    e o desconto vêm de taxa_consulta_referencia / desconto_retorno.
    """
    if ctx.get("retorno_gratuito"):
        return ctx
    if float(ctx.get("taxa_consulta") or 0) > 0.009:
        return ctx
    ref = float(ctx.get("taxa_consulta_referencia") or 0)
    if ref <= 0.009:
        return ctx
    ctx = dict(ctx)
    ctx["taxa_consulta"] = ref
    procs_soma = sum(float(p.get("valor") or 0) for p in (ctx.get("procedimentos") or []))
    ctx["subtotal"] = ref + procs_soma
    if float(ctx.get("valor_total") or 0) <= 0.009:
        ctx["valor_total"] = ctx["subtotal"]
        pago = float(ctx.get("valor_pago") or 0)
        ctx["saldo_devedor"] = max(ctx["valor_total"] - pago, 0.0)
    return ctx


def _linhas_taxa_consulta_recibo(ctx: dict) -> list[tuple[str, float]]:
    """Linha da taxa de consulta no recibo (valor de tabela quando há retorno)."""
    if ctx.get("retorno_gratuito"):
        ref = float(ctx.get("taxa_consulta_referencia") or 0)
        if ref > 0:
            return [("Taxa de consulta", ref)]
        return []
    taxa = float(ctx.get("taxa_consulta") or 0)
    if taxa <= 0:
        taxa = float(ctx.get("taxa_consulta_referencia") or 0)
    if taxa > 0:
        return [("Taxa de consulta", taxa)]
    return []


def _descontos_conhecidos_recibo(ctx: dict) -> tuple[float, float]:
    desconto_retorno = float(ctx.get("desconto_retorno") or 0)
    if desconto_retorno <= 0 and ctx.get("retorno_gratuito"):
        desconto_retorno = float(ctx.get("taxa_consulta_referencia") or 0)
    desconto = float(ctx.get("desconto") or 0)
    return desconto_retorno, desconto


def _rotulo_abatimento(procedimentos, gap: float) -> str:
    iguais = []
    for proc in procedimentos or []:
        try:
            valor = float(proc.get("valor") or 0)
        except (TypeError, ValueError):
            continue
        if abs(valor - gap) <= 0.02 and (proc.get("nome") or "").strip():
            iguais.append((proc.get("nome") or "").strip())
    if len(iguais) == 1:
        return f"Abatimento — {iguais[0]}"
    return "Abatimento"


def recebido_a_maior_recibo(ctx: dict) -> float:
    """Dinheiro recebido acima do total cobrado, sem troco lançado."""
    total = float(ctx.get("valor_total") or 0)
    pago = float(ctx.get("valor_pago") or 0)
    extra = round(pago - total, 2)
    return extra if extra > 0.009 else 0.0


def _repor_preco_que_fecha_conta(ctx: dict) -> dict:
    """Linha gravada a R$ 0 cujo preço de cadastro fecha a conta com o total cobrado."""
    desconto_retorno, desconto = _descontos_conhecidos_recibo(ctx)
    subtotal = float(ctx.get("subtotal") or 0)
    valor_total = float(ctx.get("valor_total") or 0)
    falta = round(valor_total - (subtotal - desconto_retorno - desconto), 2)
    if falta <= 0.009:
        return ctx
    procs = [dict(p) for p in (ctx.get("procedimentos") or [])]
    candidatos = []
    for proc in procs:
        valor = float(proc.get("valor") or 0)
        catalogo = float(proc.get("preco_cadastro") or 0)
        if valor <= 0.009 and abs(catalogo - falta) <= 0.02:
            candidatos.append(proc)
    if len(candidatos) != 1:
        return ctx
    candidatos[0]["valor"] = round(falta, 2)
    ctx["procedimentos"] = procs
    ctx["subtotal"] = round(subtotal + falta, 2)
    return ctx


def reconciliar_conta_recibo(ctx: dict) -> dict:
    """Fecha a conta impressa: taxa omitida entra no total; o resto vira abatimento.

    O total cobrado permanece. Se a soma dos itens menos os descontos conhecidos
    for maior, a diferença sai como linha própria (ex.: procedimento não cobrado).
    Linha a R$ 0 cujo preço de cadastro explica o total cobrado volta a esse preço.
    """
    ctx = _repor_preco_que_fecha_conta(aplicar_valor_consulta_do_local(dict(ctx)))
    desconto_retorno, desconto = _descontos_conhecidos_recibo(ctx)
    subtotal = float(ctx.get("subtotal") or 0)
    valor_total = float(ctx.get("valor_total") or 0)
    gap = round(subtotal - desconto_retorno - desconto - valor_total, 2)
    ctx.pop("abatimento", None)
    ctx.pop("abatimento_label", None)
    if gap <= 0.009:
        return ctx
    taxa = float(ctx.get("taxa_consulta") or 0)
    if taxa <= 0.009:
        taxa = float(ctx.get("taxa_consulta_referencia") or 0)
    if not ctx.get("retorno_gratuito") and taxa > 0.009 and abs(gap - taxa) <= 0.02:
        ctx["valor_total"] = round(valor_total + gap, 2)
        pago = float(ctx.get("valor_pago") or 0)
        ctx["saldo_devedor"] = round(max(ctx["valor_total"] - pago, 0.0), 2)
        return ctx
    ctx["abatimento"] = gap
    ctx["abatimento_label"] = _rotulo_abatimento(ctx.get("procedimentos"), gap)
    return ctx


def situacao_recibo(ctx: dict) -> str:
    """sem_saldo | em_aberto | parcial | quitado."""
    valor_total = float(ctx.get("valor_total") or 0)
    valor_pago = float(ctx.get("valor_pago") or 0)
    saldo = float(ctx.get("saldo_devedor", max(valor_total - valor_pago, 0)) or 0)
    if valor_total <= 0.009 and valor_pago <= 0.009:
        return "sem_saldo"
    if saldo > 0.009 and valor_pago <= 0.009:
        return "em_aberto"
    if saldo > 0.009:
        return "parcial"
    return "quitado"


def titulo_recibo(ctx: dict) -> tuple[str, str]:
    """Título e subtítulo conforme o que já foi pago."""
    situacao = situacao_recibo(ctx)
    if situacao == "sem_saldo":
        return (
            "COMPROVANTE DE ATENDIMENTO",
            "Sem saldo — consulta integralmente descontada",
        )
    if situacao == "em_aberto":
        return "COMPROVANTE DE ATENDIMENTO", "Valor em aberto"
    if situacao == "parcial":
        return "COMPROVANTE DE ATENDIMENTO", "Pagamento parcial — saldo em aberto"
    return "RECIBO DE PAGAMENTO", ""


def resumo_financeiro_recibo(ctx: dict) -> str:
    """Mantido por compatibilidade. O saldo já aparece na linha própria."""
    return ""


def _linhas_descontos_recibo(ctx: dict) -> list[tuple[str, float]]:
    """Linhas de desconto (retorno gratuito, desconto comercial e abatimento)."""
    linhas: list[tuple[str, float]] = []
    desconto_retorno, desconto = _descontos_conhecidos_recibo(ctx)
    if desconto_retorno > 0:
        linhas.append(("Desconto retorno", desconto_retorno))
    if desconto > 0:
        linhas.append(("Desconto", desconto))
    abatimento = float(ctx.get("abatimento") or 0)
    if abatimento > 0.009:
        linhas.append((ctx.get("abatimento_label") or "Abatimento", abatimento))
    return linhas
