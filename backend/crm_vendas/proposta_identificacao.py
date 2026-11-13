"""Número e validade comercial da proposta. Não cria outra sequência."""
from __future__ import annotations

from datetime import date, datetime, timedelta


def _como_data(valor):
    if valor is None:
        return None
    if isinstance(valor, datetime):
        try:
            from django.utils import timezone

            if timezone.is_aware(valor):
                valor = timezone.localtime(valor)
        except Exception:
            pass
        return valor.date()
    if isinstance(valor, date):
        return valor
    return None


def numero_proposta_exibicao(proposta) -> str:
    """Usa o número já gravado na proposta e o ano em que ela nasceu."""
    bruto = str(getattr(proposta, "numero", "") or "").strip()
    if not bruto:
        ident = getattr(proposta, "id", None)
        bruto = str(ident) if ident else ""
    if not bruto:
        return ""
    try:
        sequencia = str(int(bruto))
    except ValueError:
        sequencia = bruto
    criado = _como_data(getattr(proposta, "created_at", None))
    if criado:
        return f"{sequencia}/{criado.year}"
    return sequencia


def inicio_validade_comercial(proposta):
    marcada = _como_data(getattr(proposta, "validade_inicio", None))
    if marcada:
        return marcada
    envio = _como_data(getattr(proposta, "data_envio", None))
    if envio:
        return envio
    return _como_data(getattr(proposta, "created_at", None))


def fim_validade_comercial(proposta):
    inicio = inicio_validade_comercial(proposta)
    try:
        dias = int(getattr(proposta, "validade_dias", None))
    except (TypeError, ValueError):
        return None
    if not inicio or dias < 1:
        return None
    return inicio + timedelta(days=dias)


def comercialmente_vencida(proposta, hoje=None) -> bool:
    """Proposta assinada não vence: o documento permanece como foi assinado."""
    if getattr(proposta, "status_assinatura", "") == "concluido":
        return False
    fim = fim_validade_comercial(proposta)
    if not fim:
        return False
    return (hoje or date.today()) > fim


def texto_validade_comercial(proposta, hoje=None) -> str:
    try:
        dias = int(getattr(proposta, "validade_dias", None))
    except (TypeError, ValueError):
        return ""
    if dias < 1:
        return ""
    fim = fim_validade_comercial(proposta)
    if not fim:
        return f"Validade comercial: {dias} dias."
    data = fim.strftime("%d/%m/%Y")
    if getattr(proposta, "status_assinatura", "") == "concluido":
        return f"Validade comercial registrada: {dias} dias, até {data}."
    if comercialmente_vencida(proposta, hoje):
        return (
            f"Validade comercial encerrada em {data}. "
            "Renove a validade ou reemita a proposta. Documentos já assinados não são alterados."
        )
    return f"Validade comercial: {dias} dias, até {data}."


def frase_contratacao(servicos: str, prestadora: str = "") -> str:
    partes = [parte.strip() for parte in (servicos or "").split("•") if parte.strip()]
    if not partes:
        base = "Preparamos sua proposta comercial"
    elif len(partes) == 1:
        base = f"Preparamos sua proposta comercial para contratação do {partes[0]}"
    elif len(partes) == 2:
        base = f"Preparamos sua proposta comercial para contratação do {partes[0]} e {partes[1]}"
    else:
        meio = ", ".join(partes[1:-1])
        base = (
            f"Preparamos sua proposta comercial para contratação do {partes[0]}, "
            f"com {meio} e {partes[-1]}"
        )
    prestadora = (prestadora or "").strip()
    if prestadora:
        return f"{base}, da {prestadora}."
    return f"{base}."


def servicos_da_proposta(proposta) -> str:
    from .pdf_proposta_contrato.secoes_investimento import _itens_oportunidade
    from .pdf_proposta_contrato.formatters import subtitulo_da_versao

    oportunidade = getattr(proposta, "oportunidade", None)
    if oportunidade is None:
        return ""
    return subtitulo_da_versao(_itens_oportunidade(oportunidade))


class LinkComercialEncerrado(Exception):
    """A validade comercial acabou e o link do cliente não pode ser enviado."""


def texto_prazo_link(proposta) -> str:
    """Texto do prazo do link. Sem validade comercial, permanece 7 dias."""
    fim = fim_validade_comercial(proposta)
    if not fim:
        return "por 7 dias"
    return f"até {fim.strftime('%d/%m/%Y')}"


def delta_token_assinatura(documento, tipo, agora=None):
    """O link da proposta expira no fim da validade comercial.

    Contrato e proposta sem prazo continuam com 7 dias.
    O vendedor ainda assina se o cliente já assinou e o prazo comercial acabou.
    """
    from datetime import datetime as datahora

    if type(documento).__name__ != "Proposta" and getattr(documento, "validade_dias", None) in (None, ""):
        return timedelta(days=7)
    fim = fim_validade_comercial(documento)
    if not fim:
        return timedelta(days=7)
    if agora is None:
        try:
            from django.utils import timezone

            momento = timezone.localtime(timezone.now())
        except Exception:
            momento = datahora.now()
    elif isinstance(agora, datetime):
        momento = agora
    else:
        momento = datahora.combine(agora, datahora.min.time())
    hoje = momento.date()
    if hoje > fim:
        if tipo == "vendedor" and getattr(documento, "status_assinatura", "") == "aguardando_vendedor":
            return timedelta(days=7)
        raise LinkComercialEncerrado(
            "A validade comercial desta proposta encerrou. "
            "Renove a validade para enviar o link ao cliente."
        )
    limite = datahora.combine(fim, datahora.max.time().replace(microsecond=0))
    restante = limite - momento.replace(tzinfo=None)
    if restante.total_seconds() < 3600:
        return timedelta(hours=1)
    return restante


def validar_dias_comerciais(valor) -> int:
    try:
        dias = int(valor)
    except (TypeError, ValueError) as exc:
        raise ValueError("Informe a validade comercial em dias.") from exc
    if dias < 1 or dias > 365:
        raise ValueError("A validade comercial deve ficar entre 1 e 365 dias.")
    return dias
