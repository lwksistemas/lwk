"""Helpers de formatação e contexto do recibo de pagamento."""
import logging
import re
from decimal import Decimal, InvalidOperation

from core.cpf_utils import eh_cnpj, eh_cpf, normalizar_cpf_cnpj
from core.phone_utils import telefone_exibicao_brasileiro

from .moeda import formatar_moeda_recibo

logger = logging.getLogger(__name__)

_UNIDADE_RECIBO = {
    "ml": "mL",
    "mg": "mg",
    "g": "g",
    "un": "un",
    "ui": "UI",
    "mcg": "mcg",
    "ug": "µg",
    "µg": "µg",
}
_QTD_NO_NOME = re.compile(
    r"^(?P<nome>.*?)\s+(?P<qtd>\d+(?:[.,]\d+)?)\s*(?P<un>ml|mg|mcg|µg|ug|ui|un|g)$",
    re.IGNORECASE,
)


_MIUDAS_RECIBO = {
    "de", "da", "do", "das", "dos", "e", "em", "com", "para", "por", "a", "o", "as", "os",
}
_SIGLAS_RECIBO = {"fps", "spf", "uv", "uva", "uvb", "led", "dna", "aha", "bha"}
_UNIDADE_COLADA = re.compile(r"^(\d+(?:[.,]\d+)?)(ml|mg|mcg|µg|ug|ui|un|g)$", re.IGNORECASE)


def nome_exibicao_procedimento_recibo(nome: str) -> str:
    """Junta a dose ao procedimento e tira o caixa-alta do cadastro.

    ``PREENCHIMENTO DE GLÚTEOS 100 ML`` vira ``Preenchimento de Glúteos — 100 mL``.
    ``LIMPEZA DE PELE PROFUNDA`` vira ``Limpeza de Pele Profunda``.
    Nome que já veio com maiúsculas e minúsculas permanece.
    """
    texto = " ".join(str(nome or "").split())
    if not texto:
        return ""
    qtd = ""
    achado = _QTD_NO_NOME.match(texto)
    if achado:
        texto = achado.group("nome").strip(" -–—")
        unidade = _UNIDADE_RECIBO.get(achado.group("un").casefold(), achado.group("un"))
        qtd = f"{achado.group('qtd')} {unidade}"
    if _nome_em_caixa_alta(texto):
        texto = _frase_recibo(texto)
    if qtd:
        return f"{texto} — {qtd}"
    return texto


def _nome_em_caixa_alta(texto: str) -> bool:
    letras = [c for c in texto if c.isalpha()]
    return bool(letras) and all(c.isupper() for c in letras)


def _frase_recibo(texto: str) -> str:
    """Primeira letra de cada palavra. 'de' e 'da' ficam minúsculas, como na prévia."""
    palavras = []
    for indice, palavra in enumerate(texto.split()):
        unidade = _UNIDADE_COLADA.fullmatch(palavra)
        if unidade:
            sigla = _UNIDADE_RECIBO.get(unidade.group(2).casefold(), unidade.group(2))
            palavras.append(f"{unidade.group(1)} {sigla}")
            continue
        baixa = palavra.casefold()
        if baixa == "ph":
            palavras.append("pH")
            continue
        if baixa in _SIGLAS_RECIBO:
            palavras.append(baixa.upper())
            continue
        if indice and baixa in _MIUDAS_RECIBO:
            palavras.append(baixa)
            continue
        palavras.append(baixa[:1].upper() + baixa[1:])
    return " ".join(palavras)


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
    from clinica_beleza.retorno_service import cobrar_taxa_com_procedimento

    return {
        "taxa_consulta": taxa_consulta,
        "taxa_consulta_referencia": taxa_consulta_referencia,
        "retorno_gratuito": retorno_gratuito,
        "retorno_dias": retorno_dias,
        "retorno_aviso": retorno_aviso,
        "cobrar_taxa_com_procedimento": cobrar_taxa_com_procedimento(loja_id),
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
    logo_url = _texto_config_loja(loja, "recibo_logo")
    cor = _texto_config_loja(loja, "recibo_cor") or _texto_config_loja(loja, "cor_primaria")
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
        "cor_primaria": cor_primaria_recibo(cor),
    }


def _texto_config_loja(loja, campo: str) -> str:
    """Só texto real. Objeto simulado de teste não vira logomarca."""
    valor = getattr(loja, campo, "") if loja is not None else ""
    if not isinstance(valor, str):
        return ""
    return valor.strip()


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
        "operador_nome": (getattr(getattr(payment, "venda_balcao", None), "operador_nome", "") or "").strip(),
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


def _dados_protocolo_recibo(appointment) -> dict:
    """Valores do protocolo personalizado, para o cliente ver o desconto no recibo."""
    contrato = getattr(appointment, "protocolo_contrato", None)
    if contrato is None or getattr(contrato, "protocol_id", None):
        return {}
    try:
        bruto = round(float(contrato.valor_bruto or 0), 2)
        liquido = round(float(contrato.valor_total or 0), 2)
    except (TypeError, ValueError):
        return {}
    if bruto <= liquido + 0.009:
        return {}
    precos = []
    try:
        for linha in contrato.procedimentos.select_related("procedure").order_by("id"):
            precos.append({
                "nome": getattr(getattr(linha, "procedure", None), "nome", "") or "",
                "valor": round(float(linha.valor or 0), 2),
            })
    except Exception:
        logger.exception("Erro ao ler procedimentos do protocolo no recibo")
        precos = []
    return {
        "protocolo_valor_sem_desconto": bruto,
        "protocolo_valor_com_desconto": liquido,
        "protocolo_procedimentos": precos,
    }


def _precos_brutos_das_linhas(procs: list[dict], precos: list[dict]) -> list[dict] | None:
    """Troca o valor líquido de cada linha pelo preço do protocolo, quando os nomes batem."""
    if not procs or len(procs) != len(precos):
        return None
    usados: set[int] = set()
    saida = []
    for proc in procs:
        nome = (proc.get("nome") or "").strip().casefold()
        achou = None
        for indice, bruto in enumerate(precos):
            if indice in usados:
                continue
            if (bruto.get("nome") or "").strip().casefold() == nome and nome:
                achou = indice
                break
        if achou is None:
            return None
        usados.add(achou)
        item = dict(proc)
        item["valor"] = round(float(precos[achou].get("valor") or 0), 2)
        saida.append(item)
    soma = round(sum(item["valor"] for item in saida), 2)
    bruto = round(sum(float(item.get("valor") or 0) for item in precos), 2)
    if abs(soma - bruto) > 0.05:
        return None
    return saida


def _escalar_valores_recibo(procs: list[dict], alvo: float) -> list[dict]:
    soma = round(sum(float(p.get("valor") or 0) for p in procs), 2)
    if soma <= 0.009:
        return procs
    restante = round(alvo, 2)
    saida = []
    for indice, proc in enumerate(procs):
        item = dict(proc)
        if indice == len(procs) - 1:
            item["valor"] = round(max(restante, 0.0), 2)
        else:
            parte = round(float(proc.get("valor") or 0) / soma * alvo, 2)
            item["valor"] = parte
            restante = round(restante - parte, 2)
        saida.append(item)
    return saida


def _visita_cobra_pacote(soma: float, liquido: float) -> bool:
    """A visita cobra o pacote quando as linhas somam o valor já com desconto."""
    return abs(soma - liquido) <= 0.05


def _aplicar_desconto_do_protocolo(ctx: dict) -> dict:
    """No pagamento do pacote, as linhas voltam ao preço cheio e o desconto entra na conta.

    Na parcela, o total da visita permanece a parte da sessão. Os dois valores do
    protocolo saem à parte, para a cliente ver.
    """
    bruto = float(ctx.get("protocolo_valor_sem_desconto") or 0)
    liquido = float(ctx.get("protocolo_valor_com_desconto") or 0)
    if bruto <= liquido + 0.009:
        return ctx
    procs = [dict(p) for p in (ctx.get("procedimentos") or [])]
    soma = round(sum(float(p.get("valor") or 0) for p in procs), 2)
    valor_visita = float(ctx.get("valor_total") or 0)
    if soma <= 0.009 and valor_visita <= 0.009:
        return ctx
    ctx = dict(ctx)
    if _visita_cobra_pacote(soma, liquido) and soma > 0.009:
        ajustados = _precos_brutos_das_linhas(procs, ctx.get("protocolo_procedimentos") or [])
        if ajustados is None:
            ajustados = _escalar_valores_recibo(procs, bruto)
        taxa_parte = round(float(ctx.get("subtotal") or 0) - soma, 2)
        ctx["procedimentos"] = ajustados
        ctx["subtotal"] = round(bruto + max(taxa_parte, 0.0), 2)
        ctx["desconto_protocolo"] = round(bruto - liquido, 2)
        ctx.pop("protocolo_valores_informativos", None)
        return ctx
    ctx["protocolo_valores_informativos"] = True
    return ctx


_ROTULO_DESPESA_RECIBO = "Despesa (clínica)"
_ROTULO_CUSTEIO_RECIBO = "Custeado pela clínica"


def forma_e_custeio_clinica(metodo: str) -> bool:
    """A forma interna DESPESA, com ou sem a data entre parênteses."""
    texto = (metodo or "").strip()
    return (
        texto == _ROTULO_DESPESA_RECIBO
        or texto.startswith(_ROTULO_DESPESA_RECIBO + " ")
        or texto.startswith(_ROTULO_DESPESA_RECIBO + "(")
    )


def rotulo_forma_recibo(metodo: str) -> str:
    """No papel do paciente, custeio da clínica não aparece como forma de pagamento."""
    texto = (metodo or "").strip()
    if not forma_e_custeio_clinica(texto):
        return texto
    return _ROTULO_CUSTEIO_RECIBO + texto[len(_ROTULO_DESPESA_RECIBO):]


def custeado_pela_clinica(ctx: dict) -> bool:
    """True quando todo o valor lançado foi custeado pela clínica."""
    formas = [
        f for f in (ctx.get("formas_pagamento") or [])
        if float(f.get("valor") or 0) > 0.009
    ]
    if formas:
        return all(forma_e_custeio_clinica(str(f.get("metodo") or "")) for f in formas)
    if float(ctx.get("valor_pago") or 0) <= 0.009:
        return False
    return forma_e_custeio_clinica(str(ctx.get("metodo") or ""))


def linha_vencimento_recibo(ctx: dict) -> str:
    """Vencido quando a data já passou na emissão. Sem data, não inventa uma."""
    vencimento = (ctx.get("vencimento") or "").strip()
    if not vencimento:
        return "Sem vencimento"
    data_venc = _data_texto_recibo(vencimento)
    data_emissao = _data_texto_recibo(ctx.get("data_emissao") or ctx.get("data") or "")
    if data_venc and data_emissao and data_venc < data_emissao:
        return f"Vencido em: {vencimento}"
    return f"Vencimento: {vencimento}"


def _data_texto_recibo(texto: str):
    achado = re.search(r"(\d{2})/(\d{2})/(\d{4})", texto or "")
    if not achado:
        return None
    from datetime import date

    try:
        return date(int(achado.group(3)), int(achado.group(2)), int(achado.group(1)))
    except ValueError:
        return None


_DATA_NA_FORMA = re.compile(r"^(?P<forma>.*?)\s*\((?P<data>\d{2}/\d{2}/\d{4})\)\s*$")


def formas_detalhadas_recibo(ctx: dict) -> list[dict]:
    """Cada recebimento já gravado, com data, forma e valor separados."""
    linhas = []
    for item in ctx.get("formas_pagamento") or []:
        try:
            valor = float(item.get("valor") or 0)
        except (TypeError, ValueError):
            continue
        if valor <= 0.009:
            continue
        metodo = str(item.get("metodo") or "").strip()
        if forma_e_custeio_clinica(metodo):
            continue
        forma = str(item.get("forma") or "").strip()
        data = str(item.get("data") or "").strip()
        if not forma or not data:
            achado = _DATA_NA_FORMA.match(metodo)
            if achado:
                forma = forma or achado.group("forma").strip()
                data = data or achado.group("data")
            else:
                forma = forma or metodo
        linhas.append({
            "data": data,
            "forma": rotulo_forma_recibo(forma),
            "valor": round(valor, 2),
        })
    return linhas


def conta_com_saldo_recibo(ctx: dict) -> bool:
    """Ainda há valor a receber do paciente."""
    if comprovante_sem_cobranca(ctx):
        return False
    return situacao_recibo(ctx) in ("parcial", "em_aberto")


def rotulo_valor_conta_recibo(ctx: dict) -> str:
    if not conta_com_saldo_recibo(ctx):
        return rotulo_subtotal_recibo(ctx)
    if ctx.get("somente_produtos"):
        return "Valor total"
    return "Valor total dos procedimentos"


def _formas_pagamento_texto(ctx: dict) -> str:
    """Formata formas de pagamento para texto (WhatsApp/email)."""
    formas = ctx.get("formas_pagamento", [])
    if not formas:
        if float(ctx.get("valor_pago") or 0) <= 0.009:
            condicao = (ctx.get("condicao_cobranca") or "").strip()
            if condicao:
                return f"  Condição de cobrança: {condicao}\n"
            return ""
        metodo = rotulo_forma_recibo(ctx.get("metodo", ""))
        return f"  {metodo} — {formatar_moeda_recibo(ctx.get('valor_pago', 0))}\n"
    lines = [
        f'  • {rotulo_forma_recibo(f["metodo"])} — {formatar_moeda_recibo(f["valor"])}'
        for f in formas
    ]
    return "\n".join(lines) + "\n"


def _formas_pagamento_html(ctx: dict) -> str:
    """Formata formas de pagamento para HTML (corpo do email)."""
    formas = ctx.get("formas_pagamento", [])
    if not formas:
        metodo = rotulo_forma_recibo(ctx.get("metodo", ""))
        return f"<li>{metodo} — {formatar_moeda_recibo(ctx.get('valor_pago', 0))}</li>"
    return "".join(
        f'<li>{rotulo_forma_recibo(f["metodo"])} — {formatar_moeda_recibo(f["valor"])}</li>'
        for f in formas
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
                result.append({
                    "metodo": label,
                    "forma": METODOS.get(g["metodo_code"], g["metodo_code"]),
                    "data": g["data"].strftime("%d/%m/%Y") if hasattr(g["data"], "strftime") else "",
                    "valor": valor,
                })
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
        if nome and nome not in ("consulta", "taxa de consulta", "taxa de avaliação"):
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


def _omitir_taxa_junto_do_procedimento(ctx: dict) -> bool:
    """Clínica desligou a taxa e o atendimento tem procedimento além da consulta.

    Taxa já gravada na consulta continua no recibo (atendimento antigo).
    """
    if ctx.get("cobrar_taxa_com_procedimento") is not False:
        return False
    if float(ctx.get("taxa_consulta") or 0) > 0.009:
        return False
    return not recibo_so_consulta(ctx)


def aplicar_valor_consulta_do_local(ctx: dict) -> dict:
    """Usa a taxa do local quando a consulta ficou zerada (com ou sem procedimento).

    Fora do retorno gratuito a taxa entra no recibo sempre; no retorno a linha
    e o desconto vêm de taxa_consulta_referencia / desconto_retorno.
    Com a opção desligada, procedimento sem taxa gravada não recebe a taxa.
    """
    if ctx.get("retorno_gratuito") or _omitir_taxa_junto_do_procedimento(ctx):
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
    """Linha da taxa cobrada.

    No retorno, a taxa só entra se foi lançada na consulta. Aí o desconto
    aparece na conta. Taxa que não foi lançada não vira linha nem desconto.
    """
    if _omitir_taxa_junto_do_procedimento(ctx):
        return []
    if ctx.get("retorno_gratuito"):
        taxa = float(ctx.get("taxa_consulta") or 0)
        if taxa > 0.009 and not ctx.get("ocultar_desconto_retorno"):
            return [("Taxa de avaliação", taxa)]
        return []
    taxa = float(ctx.get("taxa_consulta") or 0)
    if taxa <= 0:
        taxa = float(ctx.get("taxa_consulta_referencia") or 0)
    if taxa > 0:
        return [("Taxa de avaliação", taxa)]
    return []


def procedimentos_exibidos_recibo(ctx: dict) -> list[tuple[str, float]]:
    """Procedimentos do cupom, com a dose junto do nome e sem consulta zerada repetida."""
    taxa_exibida = 0.0
    linhas_taxa = _linhas_taxa_consulta_recibo(ctx)
    if linhas_taxa:
        taxa_exibida = float(linhas_taxa[0][1] or 0)
    linhas: list[tuple[str, float]] = []
    for proc in ctx.get("procedimentos") or []:
        nome = nome_exibicao_procedimento_recibo(proc.get("nome") or "")
        try:
            valor = float(proc.get("valor") or 0)
        except (TypeError, ValueError):
            valor = 0.0
        if taxa_exibida > 0.009 and valor == 0.0 and nome.casefold() in (
            "consulta", "taxa de consulta", "taxa de avaliação",
        ):
            continue
        linhas.append((nome, valor))
    return linhas


def produtos_exibidos_recibo(ctx: dict) -> list[dict]:
    """Linhas de produto vendido. Insumo de procedimento não entra."""
    linhas = []
    for item in ctx.get("produtos") or []:
        try:
            subtotal = float(item.get("subtotal") or 0)
        except (TypeError, ValueError):
            subtotal = 0.0
        linhas.append({
            "nome": nome_exibicao_procedimento_recibo(item.get("nome") or "Produto"),
            "quantidade": item.get("quantidade") or "0",
            "preco_unitario": float(item.get("preco_unitario") or 0),
            "desconto": float(item.get("desconto") or 0),
            "subtotal": subtotal,
        })
    return linhas


def saldo_aberto_recibo(ctx: dict) -> float:
    valor_pago = float(ctx.get("valor_pago") or 0)
    valor_total = float(ctx.get("valor_total") or 0)
    try:
        saldo = float(ctx.get("saldo_devedor", max(valor_total - valor_pago, 0)))
    except (TypeError, ValueError):
        saldo = max(valor_total - valor_pago, 0.0)
    return saldo if saldo > 0.009 else 0.0


def _descontos_conhecidos_recibo(ctx: dict) -> tuple[float, float]:
    if ctx.get("ocultar_desconto_retorno"):
        return 0.0, float(ctx.get("desconto") or 0)
    desconto_retorno = float(ctx.get("desconto_retorno") or 0)
    if desconto_retorno <= 0 and ctx.get("retorno_gratuito"):
        cobrada = float(ctx.get("taxa_consulta") or 0)
        desconto_retorno = cobrada if cobrada > 0.009 else float(ctx.get("taxa_consulta_referencia") or 0)
    desconto = float(ctx.get("desconto") or 0)
    return desconto_retorno, desconto


def _alinhar_total_com_desconto_da_consulta(ctx: dict) -> dict:
    """Se o total ainda inclui a consulta lançada, o desconto sai desse total."""
    desconto = float(ctx.get("desconto_retorno") or 0)
    if desconto <= 0.009:
        return ctx
    subtotal = float(ctx.get("subtotal") or 0)
    valor_total = float(ctx.get("valor_total") or 0)
    if abs(subtotal - valor_total) > 0.02:
        return ctx
    ctx = dict(ctx)
    ctx["valor_total"] = round(max(0.0, valor_total - desconto), 2)
    pago = float(ctx.get("valor_pago") or 0)
    ctx["saldo_devedor"] = round(max(ctx["valor_total"] - pago, 0.0), 2)
    return ctx


def _ocultar_taxa_impressa_no_retorno(ctx: dict) -> dict:
    """Consulta lançada e descontada permanece na conta.

    Consulta que não foi lançada não ganha linha nem frase de desconto.
    O total já fechado permanece.
    """
    if not ctx.get("retorno_gratuito"):
        return ctx
    taxa_cobrada = float(ctx.get("taxa_consulta") or 0)
    if taxa_cobrada > 0.009:
        ctx = dict(ctx)
        if float(ctx.get("desconto_retorno") or 0) <= 0.009:
            ctx["desconto_retorno"] = taxa_cobrada
        return _alinhar_total_com_desconto_da_consulta(ctx)
    ref = float(ctx.get("taxa_consulta_referencia") or 0)
    if ref <= 0.009:
        ref = float(ctx.get("desconto_retorno") or 0)
    ctx = dict(ctx)
    if ref > 0.009:
        ctx["subtotal"] = round(max(0.0, float(ctx.get("subtotal") or 0) - ref), 2)
    ctx["desconto_retorno"] = 0
    ctx["taxa_consulta"] = 0
    ctx["ocultar_desconto_retorno"] = True
    return ctx


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
        return f"Abatimento — {nome_exibicao_procedimento_recibo(iguais[0])}"
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


def _desconto_comercial_sai_do_total(ctx: dict) -> dict:
    """Procedimento 1.500 e desconto 500 deixam saldo 1.000.

    Só reduz quando o total gravado ainda é o preço antes do desconto comercial.
    Se o pagamento já guardou o líquido, o total permanece.
    """
    _desconto_retorno, desconto = _descontos_conhecidos_recibo(ctx)
    if desconto <= 0.009:
        return ctx
    subtotal = float(ctx.get("subtotal") or 0)
    valor_total = float(ctx.get("valor_total") or 0)
    sem_comercial = round(subtotal - _desconto_retorno, 2)
    if abs(sem_comercial - valor_total) > 0.02:
        return ctx
    ctx = dict(ctx)
    ctx["valor_total"] = round(max(0.0, valor_total - desconto), 2)
    pago = float(ctx.get("valor_pago") or 0)
    ctx["saldo_devedor"] = round(max(ctx["valor_total"] - pago, 0.0), 2)
    return ctx


def _incorporar_desconto_da_linha_do_produto(ctx: dict) -> dict:
    """O desconto do produto sai na linha Desconto e o subtotal fica no preço cheio.

    A prévia aprovada mostra o item a R$ 300, o subtotal a R$ 300, o desconto de
    R$ 35 e o total pago a R$ 265.
    """
    bruto = 0.0
    desconto_linhas = 0.0
    for item in ctx.get("produtos") or []:
        try:
            quantidade = float(str(item.get("quantidade") or 0).replace(",", "."))
            preco = float(item.get("preco_unitario") or 0)
            desconto_item = float(item.get("desconto") or 0)
        except (TypeError, ValueError):
            continue
        if quantidade <= 0:
            continue
        bruto += quantidade * preco
        desconto_linhas += desconto_item
    bruto = round(bruto, 2)
    desconto_linhas = round(desconto_linhas, 2)
    if desconto_linhas <= 0.009 or bruto <= 0.009:
        return ctx
    desconto = round(float(ctx.get("desconto") or 0), 2)
    subtotal = round(float(ctx.get("subtotal") or 0), 2)
    if desconto + 0.02 >= desconto_linhas and subtotal + 0.05 >= bruto:
        return ctx
    # A venda de produto grava o subtotal líquido. O recibo mostra o preço cheio
    # e a linha Desconto. Não mexe quando o desconto do pagamento é outro valor.
    preco_cheio = subtotal + 0.05 < bruto and abs((subtotal + desconto_linhas) - bruto) <= 0.05
    if not preco_cheio:
        return ctx
    if desconto > 0.009 and abs(desconto - desconto_linhas) > 0.02:
        return ctx
    ctx = dict(ctx)
    ctx["subtotal"] = round(bruto, 2)
    if desconto <= 0.009:
        ctx["desconto"] = desconto_linhas
    return ctx


def reconciliar_conta_recibo(ctx: dict) -> dict:
    """Fecha a conta impressa: taxa omitida entra no total; o resto vira abatimento.

    O desconto comercial sai do total quando ainda estava somado no valor cobrado.
    Se a soma dos itens menos os descontos conhecidos for maior, a diferença sai
    como linha própria (ex.: procedimento não cobrado).
    Linha a R$ 0 cujo preço de cadastro explica o total cobrado volta a esse preço.
    O desconto do protocolo personalizado entra como linha quando a visita cobra o pacote.
    """
    ctx = _incorporar_desconto_da_linha_do_produto(ctx)
    ctx = _aplicar_desconto_do_protocolo(
        _desconto_comercial_sai_do_total(
            _repor_preco_que_fecha_conta(aplicar_valor_consulta_do_local(dict(ctx)))
        )
    )
    desconto_retorno, desconto = _descontos_conhecidos_recibo(ctx)
    desconto_protocolo = float(ctx.get("desconto_protocolo") or 0)
    subtotal = float(ctx.get("subtotal") or 0)
    valor_total = float(ctx.get("valor_total") or 0)
    gap = round(subtotal - desconto_retorno - desconto - desconto_protocolo - valor_total, 2)
    ctx.pop("abatimento", None)
    ctx.pop("abatimento_label", None)
    if gap <= 0.009:
        return _ocultar_taxa_impressa_no_retorno(ctx)
    taxa = float(ctx.get("taxa_consulta") or 0)
    if taxa <= 0.009:
        taxa = float(ctx.get("taxa_consulta_referencia") or 0)
    omitir_taxa = _omitir_taxa_junto_do_procedimento(ctx)
    if (
        not omitir_taxa
        and not ctx.get("retorno_gratuito")
        and taxa > 0.009
        and abs(gap - taxa) <= 0.02
    ):
        ctx["valor_total"] = round(valor_total + gap, 2)
        pago = float(ctx.get("valor_pago") or 0)
        ctx["saldo_devedor"] = round(max(ctx["valor_total"] - pago, 0.0), 2)
        return _ocultar_taxa_impressa_no_retorno(ctx)
    ctx["abatimento"] = gap
    ctx["abatimento_label"] = _rotulo_abatimento(ctx.get("procedimentos"), gap)
    return _ocultar_taxa_impressa_no_retorno(ctx)


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


def cor_primaria_recibo(valor: str) -> str:
    """Cor da faixa do recibo. Usa a personalização da clínica quando é um hex válido."""
    texto = (valor or "").strip()
    if re.fullmatch(r"#[0-9A-Fa-f]{6}", texto):
        return texto.upper()
    return "#8B3D52"


def tinta_recibo(cor: str, fator: float = 0.9) -> str:
    """Mistura a cor da clínica com branco para os fundos do recibo."""
    base = cor_primaria_recibo(cor)
    canais = [int(base[i:i + 2], 16) for i in (1, 3, 5)]
    mistos = [int(round(canal + (255 - canal) * fator)) for canal in canais]
    return "#{:02X}{:02X}{:02X}".format(*mistos)


def comprovante_sem_cobranca(ctx: dict) -> bool:
    """Atendimento em que o paciente não pagou: custeio da clínica ou sem valor."""
    if ctx.get("somente_produtos"):
        return False
    if custeado_pela_clinica(ctx):
        return True
    return situacao_recibo(ctx) == "sem_saldo"


def situacao_comprovante_recibo(ctx: dict) -> str:
    if custeado_pela_clinica(ctx):
        return "Custeado pela clínica"
    if situacao_recibo(ctx) == "sem_saldo":
        return "Sem valor a pagar"
    return ""


def rotulo_numero_recibo(ctx: dict) -> str:
    if comprovante_sem_cobranca(ctx):
        return "Comprovante"
    if not ctx.get("somente_produtos") and situacao_recibo(ctx) in ("parcial", "em_aberto"):
        return "Demonstrativo"
    return "Recibo"


def nota_documento_recibo(ctx: dict) -> str:
    if ctx.get("somente_produtos"):
        return "Recibo comercial de produto · Documento não fiscal"
    if comprovante_sem_cobranca(ctx):
        return "Comprovante de atendimento · Documento não fiscal."
    if situacao_recibo(ctx) in ("parcial", "em_aberto"):
        return "Demonstrativo de atendimento · Documento não fiscal."
    return "Recibo de prestação de serviços · Documento não fiscal."


def rotulo_situacao_recibo(ctx: dict) -> str:
    situacao = situacao_recibo(ctx)
    if situacao == "parcial":
        return "Parcialmente pago"
    if situacao == "em_aberto":
        return "Em aberto"
    if situacao == "quitado":
        return "Quitado"
    return "Sem valor a pagar"


def aviso_exibido_recibo(ctx: dict) -> str:
    """A frase de retorno só entra quando o atendimento ficou sem cobrança por essa regra."""
    if not ctx.get("retorno_gratuito"):
        return ""
    try:
        valor = float(ctx.get("valor_total") or 0)
        pago = float(ctx.get("valor_pago") or 0)
    except (TypeError, ValueError):
        return ""
    if valor > 0.009 or pago > 0.009:
        return ""
    return (ctx.get("retorno_aviso") or "").strip()


_UF_RECIBO = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG",
    "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
}


def texto_cadastro_recibo(texto: str) -> str:
    """Tira o caixa-alta do endereço gravado. Sigla de estado permanece."""
    texto = " ".join(str(texto or "").split())
    if not texto or not _nome_em_caixa_alta(texto):
        return texto
    palavras = []
    for indice, palavra in enumerate(texto.split()):
        nucleo = palavra.strip(",.;")
        sufixo = palavra[len(nucleo):]
        if nucleo.upper() in _UF_RECIBO and nucleo.isalpha():
            palavras.append(nucleo.upper() + sufixo)
            continue
        baixa = palavra.casefold()
        miuda = baixa.strip(",.;")
        if indice and miuda in _MIUDAS_RECIBO:
            palavras.append(baixa)
            continue
        if not baixa[:1].isalpha():
            palavras.append(palavra)
            continue
        palavras.append(baixa[:1].upper() + baixa[1:])
    return " ".join(palavras)


def titulo_recibo(ctx: dict) -> tuple[str, str]:
    """Título do documento. Pendência e gratuidade não usam o nome de recibo quitado."""
    if ctx.get("somente_produtos"):
        return "RECIBO DE VENDA DE PRODUTOS", ""
    if custeado_pela_clinica(ctx):
        return "COMPROVANTE DE ATENDIMENTO", ""
    situacao = situacao_recibo(ctx)
    if situacao == "sem_saldo":
        return "COMPROVANTE DE ATENDIMENTO — SEM VALOR A PAGAR", ""
    if situacao == "em_aberto":
        return "DEMONSTRATIVO DE ATENDIMENTO — PAGAMENTO PENDENTE", ""
    if situacao == "parcial":
        return "DEMONSTRATIVO DE ATENDIMENTO — PAGAMENTO PARCIAL", ""
    return "RECIBO DE PAGAMENTO — ATENDIMENTO", ""


def resumo_financeiro_recibo(ctx: dict) -> str:
    """Mantido por compatibilidade. O saldo já aparece na linha própria."""
    return ""


def _outro_desconto_na_conta(ctx: dict) -> bool:
    desconto_retorno, desconto = _descontos_conhecidos_recibo(ctx)
    if desconto_retorno > 0.009 or desconto > 0.009:
        return True
    return float(ctx.get("abatimento") or 0) > 0.009


def rotulo_subtotal_recibo(ctx: dict) -> str:
    if float(ctx.get("desconto_protocolo") or 0) > 0.009:
        return "Valor sem desconto"
    return "Subtotal"


def rotulo_total_recibo(ctx: dict) -> str:
    if float(ctx.get("desconto_protocolo") or 0) > 0.009 and not _outro_desconto_na_conta(ctx):
        return "Valor com desconto"
    return "Total"


def linha_valor_com_desconto_recibo(ctx: dict) -> tuple[str, float] | None:
    """Quando ainda há outro desconto, o líquido do protocolo sai numa linha própria."""
    if float(ctx.get("desconto_protocolo") or 0) <= 0.009 or not _outro_desconto_na_conta(ctx):
        return None
    return ("Valor com desconto", float(ctx.get("protocolo_valor_com_desconto") or 0))


def linhas_protocolo_informativo(ctx: dict) -> list[tuple[str, float]]:
    """Parcela da sessão: os dois valores do protocolo, sem alterar o total da visita."""
    if not ctx.get("protocolo_valores_informativos"):
        return []
    bruto = float(ctx.get("protocolo_valor_sem_desconto") or 0)
    liquido = float(ctx.get("protocolo_valor_com_desconto") or 0)
    if bruto <= liquido + 0.009:
        return []
    return [
        ("Valor sem desconto", bruto),
        ("Valor com desconto", liquido),
    ]


def _linhas_descontos_recibo(ctx: dict) -> list[tuple[str, float]]:
    """Linhas de desconto (retorno gratuito, protocolo, desconto comercial e abatimento)."""
    linhas: list[tuple[str, float]] = []
    desconto_retorno, desconto = _descontos_conhecidos_recibo(ctx)
    if desconto_retorno > 0:
        linhas.append(("Desconto da avaliação", desconto_retorno))
    desconto_protocolo = float(ctx.get("desconto_protocolo") or 0)
    if desconto_protocolo > 0.009:
        linhas.append(("Desconto do protocolo", desconto_protocolo))
    if desconto > 0:
        linhas.append(("Desconto", desconto))
    abatimento = float(ctx.get("abatimento") or 0)
    if abatimento > 0.009:
        linhas.append((ctx.get("abatimento_label") or "Abatimento", abatimento))
    return linhas
