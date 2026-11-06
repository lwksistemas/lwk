"""Título, situação e rótulos do comprovante."""
from .conta_recibo import rotulo_subtotal_recibo
from .pagamento_recibo import custeado_pela_clinica


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
