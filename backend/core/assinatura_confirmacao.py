"""Confirmação exibida quando o link de assinatura é aberto de novo."""
from django.utils import timezone


def data_hora_assinatura(quando) -> tuple[str, str]:
    if quando is None or not hasattr(quando, "strftime"):
        return "", ""
    local = timezone.localtime(quando) if timezone.is_aware(quando) else quando
    return local.strftime("%d/%m/%Y"), local.strftime("%H:%M")


def confirmacao_assinatura(rotulo: str, nome: str, quando, *, tipo_documento: str) -> dict:
    """Proposta assinada digitalmente por NOME em DATA às HORA."""
    data, hora = data_hora_assinatura(quando)
    nome = " ".join((nome or "").split())
    particípio = "assinada" if rotulo.strip().lower() == "proposta" else "assinado"
    mensagem = f"{rotulo} {particípio} digitalmente"
    if nome:
        mensagem += f" por {nome}"
    if data and hora:
        mensagem += f" em {data} às {hora}"
    elif data:
        mensagem += f" em {data}"
    mensagem += "."
    return {
        "ja_assinado": True,
        "error_code": "ja_assinado",
        "tipo_documento": tipo_documento,
        "tipo_documento_display": rotulo,
        "nome_cliente": nome,
        "data": data,
        "hora": hora,
        "mensagem": mensagem,
    }
